
class NetworkMapKQL:
    @staticmethod
    def vnet_resource_graph_query():

      return '''
        resources
        | where type == "microsoft.network/virtualnetworks"
        | extend VNet = name
        | mv-expand addressPrefixes = properties.addressSpace.addressPrefixes
        | mv-expand subnet = properties.subnets
        | project VNet, VNetAddressSpace = addressPrefixes, SubnetName=subnet.name, SubnetAddressPrefix=subnet.properties.addressPrefix
      '''

    @staticmethod
    def vnet_flow_without_externalpublic_malicious_query(flow_types: list[str] = []):

      ft = ', '.join([f"'{flow_type}'" for flow_type in flow_types])
      flowType = ft if flow_types else "''"

      return f'''


let traffic_analytics_pip_table = NTAIpDetails
              | project ['PublicIP']=Ip, ['PIP_PublicIpDetails']=PublicIpDetails, ['PIP_ThreatType']=ThreatType, ['PIP_Location']=Location, ['PIP_Url']=Url, ['PIP_ThreatDescription']=ThreatDescription;


NTANetAnalytics

| where (FlowType != '' and SubType == 'FlowLog')


| where FlowType in ({flowType})

| take 9000

| extend SrcPIP = substring(SrcPublicIps, 0, indexof(SrcPublicIps, "|"))
| extend DestPIP = substring(DestPublicIps, 0, indexof(DestPublicIps, "|"))

| extend SrcSubnetSplitted =  split(SrcSubnet, '/')
| extend SrcRG = tostring(SrcSubnetSplitted[0])
| extend SrcVNet = tostring(SrcSubnetSplitted[1])
| extend SrcSubnetName = tostring(SrcSubnetSplitted[2])

| extend DestSubnetSplitted =  split(DestSubnet, '/')
| extend DestRG = tostring(DestSubnetSplitted[0])
| extend DestVNet = tostring(DestSubnetSplitted[1])
| extend DestSubnetName = tostring(DestSubnetSplitted[2])


// resolve Azure Public IP from NTAIpDetails table
| join kind=leftouter
(
    traffic_analytics_pip_table
| project 
    ['SrcPIP_Ip']=PublicIP, 
    ['AzurePublic_Src_PublicIpDetails']=PIP_PublicIpDetails, 
    ['AzurePublic_SrcPIP_Location']=PIP_Location,
    ['Malicious_SrcPIP_Url']=PIP_Url,
    ['Malicious_SrcPIP_ThreatType']=PIP_ThreatType, 
    ['Malicious_SrcPIP_ThreatDescription']=PIP_ThreatDescription
)
on $left.SrcPIP == $right.SrcPIP_Ip

| join kind=leftouter
(
    traffic_analytics_pip_table
    | project
        ['DestPIP_Ip']=PublicIP, 
        ['AzurePublic_Dest_PublicIpDetails']=PIP_PublicIpDetails,
        ['AzurePublic_DestPIP_Location']=PIP_Location, 
        ['Malicious_DestPIP_Url']=PIP_Url, 
        ['Malicious_DestPIP_ThreatType']=PIP_ThreatType, 
        ['Malicious_DestPIP_ThreatDescription']=PIP_ThreatDescription
)
on $left.DestPIP == $right.DestPIP_Ip

// set SrcPIP_Ip if exist
| extend SrcIp = iif(SrcPIP_Ip != '', SrcPIP_Ip, SrcIp)
// set DestPIP_Ip if exist
| extend DestIp = iif(DestPIP_Ip != '', DestPIP_Ip, DestIp)


// resolve SrcName as private endpoint name if traffic is private endpoint
// *note: private endpoint is Source and not destination
| extend PrivateEndpointName = split(PrivateEndpointResourceId, '/')[-1]
| extend PrivateLinkName = split(PrivateEndpointResourceId, '/')[-2]

| extend SrcNodeType = iif(SrcApplicationGateway != '', 'APPGW',
                       iif(SrcLoadBalancer != '', 'ALB',
                       iif(SrcExpressRouteCircuit != '', 'EXPRESSROUTE',
                       iif(FlowType == 'AzurePublic' and AzurePublic_Src_PublicIpDetails != '', 'PAAS',
                       iif(SrcSubnetName == 'azurebastionsubnet', 'BASTION',
                       iif(PrivateEndpointResourceId != '' and PrivateLinkResourceId != '',  'PRIVATEENDPOINT',
                       iif(FlowType == 'ExternalPublic' and FlowDirection == 'Inbound' and Malicious_SrcPIP_ThreatType != '', 'EXTERNALPUBLICMALICIOUS', 
                       iif(FlowType == 'ExternalPublic' and FlowDirection == 'Inbound', 'INTERNET', 
                       iif(FlowType == 'MaliciousFlow'and FlowDirection == 'Inbound', 'MALICIOUSFLOW', 'NODE')))))))))

| extend SrcName = iif(SrcApplicationGateway != '', SrcApplicationGateway,
                   iif(SrcLoadBalancer != '', SrcLoadBalancer,
                   iif(AzurePublic_Src_PublicIpDetails != '', AzurePublic_Src_PublicIpDetails,
                   iif(SrcExpressRouteCircuit != '', 'expressroute-node',
                   iif(SrcSubnetName == 'azurebastionsubnet', 'bastion-vm',
                   iif(PrivateEndpointResourceId != '' and PrivateLinkResourceId != '',  PrivateEndpointName,
                   iif(SrcNic startswith 'unknown', strcat('managed vm in ', iif(SrcSubnetName has 'subnet', SrcSubnetName, strcat(SrcSubnetName, ' subnet'))),
                         iif(SrcVm != '', SrcVm, '-' ))))))))

| extend SrcName = iif(indexof(SrcName, '/',0) > 0, split(SrcName, '/')[-1], SrcName)

| extend DestNodeType = iif(DestApplicationGateway != '', 'APPGW',
                        iif(DestLoadBalancer != '', 'ALB',
                        iif(DestExpressRouteCircuit != '', 'EXPRESSROUTE',
                        iif(FlowType == 'AzurePublic' and AzurePublic_Dest_PublicIpDetails != '', 'PAAS',
                        iif(DestSubnetName == 'azurebastionsubnet', 'BASTION',
                        iif(PrivateEndpointResourceId != '' and PrivateLinkResourceId != '',  'PRIVATEENDPOINT',
                        iif(FlowType == 'ExternalPublic' and FlowDirection == 'Outbound' and Malicious_DestPIP_ThreatType != '', 'EXTERNALPUBLICMALICIOUS',
                        iif(FlowType == 'ExternalPublic' and FlowDirection == 'Outbound', 'INTERNET', 
                        iif(FlowType == 'MaliciousFlow' and FlowDirection == 'Outbound', 'MALICIOUSFLOW', 'NODE')))))))))

| extend DestName = iif(DestApplicationGateway != '', DestApplicationGateway,
                     iif(DestLoadBalancer != '', DestLoadBalancer,
                      iif(AzurePublic_Dest_PublicIpDetails != '', AzurePublic_Dest_PublicIpDetails,
                       iif(DestExpressRouteCircuit != '', 'expressroute-node', 
                       iif(DestSubnetName == 'azurebastionsubnet', 'bastion-vm',
                        iif(PrivateEndpointResourceId != '' and PrivateLinkResourceId != '',  PrivateLinkName,
                         iif(DestNic startswith 'unknown', strcat('managed vm in ', iif(DestSubnetName has 'subnet', DestSubnetName, strcat(DestSubnetName, ' subnet'))),
                          iif(DestVm != '',  DestVm, '' ))))))))


| extend DestName = iif(indexof(DestName, '/',0) > 0, split(DestName, '/')[-1], DestName)

| extend protocol = tolower(strcat(L4Protocol,  iif(L7Protocol != 'Unknown', strcat(':', L7Protocol), '')))

// external public only
| extend ExternalPublic_Src_Country = iif(FlowType == 'ExternalPublic' and FlowDirection == 'Inbound', Country, '')
| extend ExternalPublic_Dest_Country = iif(FlowType == 'ExternalPublic' and FlowDirection == 'Outbound', Country, '')

| extend NSG = iif(AclGroup startswith '/', AclGroup, '')
| extend NSGRule = iif(AclGroup startswith '/', AclRule, '')


| summarize 
    BytesSrcToDest = max(BytesSrcToDest),
    BytesDestToSrc = max(BytesDestToSrc),
    TimeGenerated = max(TimeGenerated) by
    
    FlowType, 
    FlowDirection,
    FlowEncryption,
    ConnectionType, 
    protocol,
    IsFlowCapturedAtUdrHop,
    NSG,
    NSGRule,
    
    SrcNodeType,
    AzurePublic_SrcPIP_Location, 
    ExternalPublic_Src_Country, 
    SrcSubscription, 
    SrcRG, 
    SrcVNet, 
    SrcSubnetName, 
    SrcIp,
    SrcName,
    
    DestNodeType,
    AzurePublic_DestPIP_Location, 
    ExternalPublic_Dest_Country, 
    DestSubscription, 
    DestRG, 
    DestVNet, 
    DestSubnetName,
    DestIp,
    DestPort,
    DestName,

    Malicious_SrcPIP_Url,
    Malicious_SrcPIP_ThreatType,
    Malicious_SrcPIP_ThreatDescription,

    Malicious_DestPIP_Url,
    Malicious_DestPIP_ThreatType,
    Malicious_DestPIP_ThreatDescription


| extend SrcToDestDataSize = format_bytes(BytesSrcToDest, 2)
| extend DestToSrcDataSize = format_bytes(BytesDestToSrc, 2)

| distinct 

    TimeGenerated,
    FlowType, 
    FlowDirection,
    FlowEncryption,
    ConnectionType, 
    protocol,
    IsFlowCapturedAtUdrHop,
    SrcToDestDataSize,
    DestToSrcDataSize,
    NSG,
    NSGRule,
    
    SrcNodeType,
    AzurePublic_SrcPIP_Location, 
    ExternalPublic_Src_Country, 
    SrcSubscription, 
    SrcRG, 
    SrcVNet, 
    SrcSubnetName, 
    SrcIp,
    SrcName,
    
    DestNodeType,
    AzurePublic_DestPIP_Location, 
    ExternalPublic_Dest_Country, 
    DestSubscription, 
    DestRG, 
    DestVNet, 
    DestSubnetName,
    DestIp,
    DestPort,
    DestName,

    Malicious_SrcPIP_Url,
    Malicious_SrcPIP_ThreatType,
    Malicious_SrcPIP_ThreatDescription,

    Malicious_DestPIP_Url,
    Malicious_DestPIP_ThreatType,
    Malicious_DestPIP_ThreatDescription

      '''