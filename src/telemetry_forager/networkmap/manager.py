from config import AppConfig
from azure.monitor.query import LogsQueryClient
from azure.monitor.query._models import LogsQueryStatus
from azure.identity import DefaultAzureCredential
import datetime
from datetime import datetime, timedelta, timezone
import pandas as pd
import log as Log
from azure.core.exceptions import HttpResponseError
from .kql import NetworkMapKQL
from .model import NetworkMapResult, FilterDataResult
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import *
import json
import time



class NetworkMapManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.kql = NetworkMapKQL()
        self.azcred = DefaultAzureCredential()
        self.law_client = LogsQueryClient(self.azcred )
        self.rg_client = ResourceGraphClient(credential=self.azcred)


    def get_network_map(self,  start_time: datetime, 
                               end_time: datetime,
                               flow_types: list[str] = [],
                               flow_direction: str = 'all',
                               src_subscrition: list[str] = [],
                               dest_subscription: list[str] = [],
                               src_rg: list[str] = [],
                               dest_rg: list[str] = [],
                               src_vnet: list[str] = [],
                               dest_vnet: list[str] = [],
                               src_subnet: list[str] = [],
                               dest_subnet: list[str] = [],
                               src_ip: list[str] = [],
                               dest_ip: list[str] = [],
                               duration: list[int] = [],
                               src_payload_size: list[str] = [],
                               dest_payload_size: list[str] = [],
                               row_limit = 5000) -> NetworkMapResult:
        

        try:

            kql_query = self.kql.vnet_flow_logs_kql(flow_types=flow_types, flow_direction=flow_direction, row_limit=row_limit)

            maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        
            self._resolve_src_dest_name_for_unknown_traffic(maindf)

            maindf = self._apply_filter_src_subscription(maindf, src_subscrition)

            maindf = self._apply_filter_src_rg(maindf, src_rg)

            maindf = self._apply_filter_dest_subscription(maindf, dest_subscription)

            maindf = self._apply_filter_dest_rg(maindf, dest_rg)

            maindf = self._apply_filter_src_vnet(maindf, src_vnet)

            maindf = self._apply_filter_src_subnet(maindf, src_subnet)

            maindf = self._apply_filter_dest_vnet(maindf, dest_vnet)

            maindf = self._apply_filter_dest_subnet(maindf, dest_subnet)

            maindf = self._apply_filter_src_ip(maindf, src_ip)

            maindf = self._apply_filter_dest_ip(maindf, dest_ip)

            maindf = self._apply_filter_estimated_duration_sec(maindf, duration)

            maindf = self._apply_filter_src_payload_size(maindf, src_payload_size)

            maindf = self._apply_filter_dest_payload_size(maindf, dest_payload_size)

            # create nodes, edges and categories for echart
            nodes = self._create_echart_nodes(maindf=maindf)

            edges = self._create_echart_edges(maindf=maindf)

            categories = self._create_echart_categories(maindf=maindf)
            
            nmap = NetworkMapResult(nodes=nodes, edges=edges, categories=categories)

            return nmap

        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}
        

        
    def get_filter_data(self, start_time: datetime, 
                               end_time: datetime,
                               flow_types: list[str] = [],
                               flow_direction: str = 'all',
                               row_limit = 5000) -> FilterDataResult:

        try:

            kql_query = self.kql.vnet_flow_logs_kql(flow_types=flow_types, flow_direction=flow_direction, row_limit=row_limit)

            maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        
            self._resolve_src_dest_name_for_unknown_traffic(maindf)

            src_subscription = self._create_unique_src_subscription(maindf=maindf)

            src_rg = self._create_unique_src_rg(maindf=maindf)

            src_vnet = self._create_unique_src_vnet(maindf=maindf)

            src_subnet = self._create_unique_src_subnet(maindf=maindf)

            src_ip = self._create_unique_src_ip(maindf=maindf)

            dest_subscription = self._create_unique_dest_subscription(maindf=maindf)

            dest_rg = self._create_unique_dest_rg(maindf=maindf)

            dest_vnet = self._create_unique_dest_vnet(maindf=maindf)

            dest_subnet = self._create_unique_dest_subnet(maindf=maindf)

            dest_ip = self._create_unique_dest_ip(maindf=maindf)

            estimated_duration_sec = self._create_unique_estimated_duration_sec(maindf=maindf)

            src_payload_size = self._create_unique_src_payload_size(maindf=maindf)

            dest_payload_size = self._create_unique_dest_payload_size(maindf=maindf)

            fd = FilterDataResult(src_subscription=src_subscription,
                                  src_rg=src_rg,
                                  src_vnet=src_vnet,
                                  src_subnet=src_subnet,
                                  src_ip=src_ip,
                                  dest_subscription=dest_subscription,
                                  dest_rg=dest_rg,
                                  dest_vnet=dest_vnet,
                                  dest_subnet=dest_subnet,
                                  dest_ip=dest_ip,
                                  estimated_duration_sec=estimated_duration_sec,
                                  src_payload_size=src_payload_size,
                                  dest_payload_size=dest_payload_size)

            return fd
        
        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
    


    def _create_echart_nodes(self, maindf: pd.DataFrame) -> dict:

        src_nodes_final_df = pd.DataFrame()
        src_nodes_final_df['timeGenerated'] = maindf['TimeGenerated']
        src_nodes_final_df['id'] = maindf['SrcIp']
        src_nodes_final_df['name'] = maindf['SrcName']
        src_nodes_final_df['category'] = maindf['FlowType']
        src_nodes_final_df['subscription'] = maindf['SrcSubscription']
        src_nodes_final_df['rg'] = maindf['SrcRG'] 
        src_nodes_final_df['nodeType'] = maindf['SrcNodeType']
        src_nodes_final_df['ip'] = maindf['SrcIp']
        src_nodes_final_df['subnet'] = maindf['SrcSubnetName']
        src_nodes_final_df['vnet'] = maindf['SrcVNet']
        src_nodes_final_df['azurePublicPIPLocation'] = maindf['AzurePublic_SrcPIP_Location']
        src_nodes_final_df['externalPublicCountry'] = maindf['ExternalPublic_Src_Country']
        src_nodes_final_df['maliciousSrcPIPUrl'] = maindf['Malicious_SrcPIP_Url']
        src_nodes_final_df['maliciousSrcPipThreatType'] = maindf['Malicious_SrcPIP_Url']
        src_nodes_final_df['maliciousSrcPIPThreatDescription'] = maindf['Malicious_SrcPIP_ThreatDescription']

        dest_nodes_final_df = pd.DataFrame()
        dest_nodes_final_df['timeGenerated'] = maindf['TimeGenerated']
        dest_nodes_final_df['id'] = maindf['DestIp']
        dest_nodes_final_df['name'] = maindf['DestName']
        dest_nodes_final_df['category'] = maindf['FlowType']
        dest_nodes_final_df['subscription'] = maindf['DestSubscription']
        dest_nodes_final_df['rg'] = maindf['DestRG']
        dest_nodes_final_df['nodeType'] = maindf['DestNodeType']
        dest_nodes_final_df['ip'] = maindf['DestIp']
        dest_nodes_final_df['destPort'] = maindf['DestPort']
        dest_nodes_final_df['subnet'] = maindf['DestSubnetName']
        dest_nodes_final_df['vnet'] = maindf['DestVNet']
        dest_nodes_final_df['azurePublicPIPLocation'] = maindf['AzurePublic_DestPIP_Location']
        dest_nodes_final_df['externalPublicCountry'] = maindf['ExternalPublic_Dest_Country']
        dest_nodes_final_df['maliciousDestPIPUrl'] = maindf['Malicious_DestPIP_Url']
        dest_nodes_final_df['maliciousDestPIPThreatType'] = maindf['Malicious_DestPIP_ThreatType']
        dest_nodes_final_df['maliciousDestPIPThreatDescription'] = maindf['Malicious_DestPIP_ThreatDescription']


        # id,title,subtitle,mainstat,secondarystat,color
        combined_list = [src_nodes_final_df, dest_nodes_final_df]

        final_nodes_df = pd.concat(combined_list)

        final_nodes_df = final_nodes_df.drop_duplicates(subset=['id'])

        final_nodes_json_str =  final_nodes_df.to_json(orient='records')

        result = json.loads(final_nodes_json_str)

        return result
    
    def _create_echart_edges(self, maindf: pd.DataFrame) -> dict:

        edges_df = pd.DataFrame()
        edges_df['timeGenerated'] = maindf['TimeGenerated']
        edges_df['nsg'] = maindf['NSG']
        edges_df['nsgRule'] = maindf['NSGRule']
        edges_df['category'] = maindf['FlowType']
        edges_df['source'] = maindf['SrcIp']
        edges_df['target'] = maindf['DestIp']

        edges_df['src_to_dest_data_size'] = maindf['SrcToDestDataSize']
        edges_df['dest_to_srct_data_size'] = maindf['DestToSrcDataSize']
        edges_df['flowType'] = maindf['FlowType']
        edges_df['flowDirection'] = maindf['FlowDirection']
        edges_df['flowEncryption'] = maindf['FlowEncryption']
        edges_df['protocol'] = maindf['protocol']
        edges_df['connectionType'] = maindf['ConnectionType']
        edges_df['isUDRHop'] = maindf['IsFlowCapturedAtUdrHop']

        edges_df['numberOfRequests'] = maindf['NumberOfRequests']
        edges_df['estAvgDurationSec'] = maindf['EstAvgDurationSec']
        edges_df['flowStartTime'] = maindf['FlowStartTime']
        edges_df['flowEndTime'] = maindf['FlowEndTime']

        edges_df = edges_df.drop_duplicates(subset=['source', 'target'])

        final_edges_json_str =  edges_df.to_json(orient='records')

        result = json.loads(final_edges_json_str)

        return result   

    def _create_echart_categories(self, maindf: pd.DataFrame) -> dict:
        tempdf = pd.DataFrame()
        tempdf['name'] = maindf['FlowType'].unique()
        result =  tempdf.to_json(orient='records')
        return result
    
    def _create_unique_src_subscription(self, maindf: pd.DataFrame) -> dict:
        maindf = maindf.drop_duplicates(subset=['SrcIp', 'DestIp'], keep='first')
        
        tempdf = maindf.drop_duplicates('SrcSubscription', keep='first')
        tempdf = tempdf[tempdf['SrcSubscription'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['SrcSubscription']

        return result.to_dict(orient='records')  

    def _create_unique_src_rg(self, maindf: pd.DataFrame) -> dict:
        
        tempdf = maindf.drop_duplicates('SrcRG', keep='first')
        tempdf = tempdf[tempdf['SrcRG'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['SrcRG']
        
        return result.to_dict(orient='records')

    def _create_unique_src_vnet(self, maindf: pd.DataFrame) -> dict:
        tempdf = maindf.drop_duplicates('SrcVNet', keep='first')
        tempdf = tempdf[tempdf['SrcVNet'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['SrcVNet']
            
        return result.to_dict(orient='records')

    def _create_unique_src_subnet(self, maindf: pd.DataFrame) -> dict:
        
        tempdf = pd.DataFrame()
        tempdf['SrcVNet'] = maindf['SrcVNet']
        tempdf['SrcSubnetName'] = maindf['SrcSubnetName'].str.lower()
        tempdf = tempdf.drop_duplicates('SrcSubnetName', keep='first')
        tempdf = tempdf[(tempdf['SrcVNet'] != '') & (tempdf['SrcSubnetName'] != '')]

        temp_result = pd.DataFrame()
        temp_result = tempdf[['SrcVNet', 'SrcSubnetName']]

        result = pd.DataFrame()
        result['DisplayName'] = temp_result.apply(lambda x: ' / '.join(x.dropna()), axis=1)
        result['SubnetName'] = temp_result['SrcSubnetName']
        
        return result.to_dict(orient='records')  

    def _create_unique_src_ip(self, maindf: pd.DataFrame) -> dict:

        maindf = maindf.drop_duplicates('SrcIp', keep='first')
        maindf= maindf[maindf['SrcIp'] != '']

        tempdf = pd.DataFrame()
        tempdf['SrcName '] = maindf['SrcName']
        tempdf['SrcIp'] = maindf['SrcIp']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf.apply(lambda x: ' / '.join(x.dropna()), axis=1)
        result['SrcIp'] = tempdf['SrcIp']
        
        return result.to_dict(orient='records')
    
    def _create_unique_dest_subscription(self, maindf: pd.DataFrame) -> dict:
        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('DestSubscription', keep='first')
        tempdf = tempdf[tempdf['DestSubscription'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['DestSubscription']
        
        return result.to_dict(orient='records')
    
    def _create_unique_dest_rg(self, maindf: pd.DataFrame) -> dict:

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('DestRG', keep='first')
        tempdf = tempdf[tempdf['DestRG'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['DestRG']
        
        return result.to_dict(orient='records')
 
    def _create_unique_dest_vnet(self, maindf: pd.DataFrame) -> dict:

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('DestVNet', keep='first')
        tempdf = tempdf[tempdf['DestVNet'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['DestVNet']
        
        return result.to_dict(orient='records')

    def _create_unique_dest_subnet(self, maindf: pd.DataFrame) -> dict:
        tempdf = pd.DataFrame()
        tempdf['DestVNet'] = maindf['DestVNet']
        tempdf['DestSubnetName'] = maindf['DestSubnetName'].str.lower()
        tempdf = tempdf.drop_duplicates('DestSubnetName', keep='first')
        tempdf = tempdf[(tempdf['DestVNet'] != '') & (tempdf['DestSubnetName'] != '')]

        temp_result = pd.DataFrame()
        temp_result = tempdf[['DestVNet', 'DestSubnetName']]

        result = pd.DataFrame()
        result['DisplayName'] = temp_result.apply(lambda x: ' / '.join(x.dropna()), axis=1)
        result['SubnetName'] = temp_result['DestSubnetName']

        return result.to_dict(orient='records')
     
    def _create_unique_dest_ip(self, maindf: pd.DataFrame) -> dict:
        
        maindf = maindf.drop_duplicates('DestIp', keep='first')
        maindf= maindf[maindf['DestIp'] != '']

        tempdf = pd.DataFrame()
        tempdf['DestName '] = maindf['DestName']
        tempdf['DestIp'] = maindf['DestIp']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf.apply(lambda x: ' / '.join(x.dropna()), axis=1)
        result['DestIp'] = tempdf['DestIp']
        
        return result.to_dict(orient='records')
    
    def _create_unique_estimated_duration_sec(self, maindf: pd.DataFrame) -> dict:

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('EstAvgDurationSec', keep='first')

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['EstAvgDurationSec']

        result = result.sort_values(by='DisplayName', ascending=False)
        
        return result.to_dict(orient='records')
    
    def _create_unique_src_payload_size(self, maindf: pd.DataFrame) -> dict:

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('SrcToDestDataSize', keep='first')

        result = pd.DataFrame()
        result['BytesSrcToDest'] = tempdf['BytesSrcToDest']
        result['DisplayName'] = tempdf['SrcToDestDataSize']

        result = result.sort_values(by='BytesSrcToDest', ascending=False)

        result = result.drop('BytesSrcToDest', axis=1)
        
        return result.to_dict(orient='records')
    
    def _create_unique_dest_payload_size(self, maindf: pd.DataFrame) -> dict:

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('SrcToDestDataSize', keep='first')

        result = pd.DataFrame()
        result['BytesDestToSrc'] = tempdf['BytesDestToSrc']
        result['DisplayName'] = tempdf['DestToSrcDataSize']

        result = result.sort_values(by='BytesDestToSrc', ascending=False)

        result = result.drop('BytesDestToSrc', axis=1)
        
        return result.to_dict(orient='records')
    
    def _get_main_dataframe(self, kql_query, start_time, end_time) -> pd.DataFrame:

        try:

            df = self._get_vnet_flow_log(kql_query=kql_query, start_time=start_time, end_time=end_time)

            # update SrcName with Subnet name if SrcName is empty        
            df['SrcName'] = df.apply(lambda x: x['SrcSubnetName'] if x['SrcName']=='' else x['SrcName'], axis=1)

            maindf = df.drop_duplicates(subset=['SrcIp', 'DestIp']) #df.drop_duplicates(subset=['SrcName', 'DestName'])

            #maindf['timeGenerated'] = maindf['TimeGenerated'].dt.strftime("%a %d %b %Y %H:%M:%S")
            maindf['FlowStartTime'] = maindf['FlowStartTime'].dt.strftime("%a %d %b %Y %H:%M:%S")
            maindf['FlowEndTime'] = maindf['FlowEndTime'].dt.strftime("%a %d %b %Y %H:%M:%S")

            maindf.fillna('', inplace=True)

            return maindf

        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}

    def _get_vnet_flow_log(self, kql_query, start_time, end_time) -> pd.DataFrame:

        try:

            df = pd.DataFrame()

            start_time = start_time.astimezone(timezone.utc)
            end_time = end_time.astimezone(timezone.utc)

            if self.config.networkmap_workspace_id:

                response =  self.law_client.query_workspace(
                            workspace_id= self.config.networkmap_workspace_id,
                            query=kql_query,
                            timespan=(start_time, end_time)
                        )

                if response.status == LogsQueryStatus.SUCCESS:
                    table = response.tables[0]
                    df = pd.DataFrame(data=table.rows, columns=table.columns)
                    #result = df.to_dict(orient='records')

            return df

        except HttpResponseError as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}
        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}
        
    def _get_existing_vnets(self):
            
            # get subscription ids
            sub_client = SubscriptionClient(self.azcred)
            subscription_list = sub_client.subscriptions.list()
            subids = [item.subscription_id for item in subscription_list]

            resourcegraph_client = ResourceGraphClient(credential=self.azcred)

            kql_query = self.kql.vnet_resource_graph_query()

            # Create Azure Resource Graph client and set options
            query = QueryRequest(
                        query=kql_query,
                        subscriptions=subids,
                        options=QueryRequestOptions(
                            result_format=ResultFormat.TABLE
                        )
                    )
            query_response = resourcegraph_client.resources(query)


            data_cols = [x['name'] for x in query_response.data['columns']]
            data_row = query_response.data['rows']
            vnets = pd.DataFrame(data_row, columns=data_cols)

            return vnets

    # TBD the usefulness of trying to resolve src and dest name with existing vnets.
    # Performance is a major concern here.
    def _resolve_src_dest_name_for_unknown_traffic(self, maindf: pd.DataFrame):
        """
        Resolve the source and destination names for known traffic.
        *in-place update of maindf
        """

        try:

            # vnets = self._get_existing_vnets()

            # # resolve vnet name and subnet name in maind from existing vnets
            # for index, ukprow in maindf.iterrows():

            #     srcip = ukprow['SrcIp']
            #     srcname = ukprow['SrcName']
            #     destip = ukprow['DestIp']
            #     destname= ukprow['DestName']

            #     if srcname == '':
            #         for index, vnet_subnet in vnets.iterrows():
            #             subnet_cidr = vnet_subnet['SubnetAddressPrefix']
            #             vnet_name = vnet_subnet['VNet']
            #             subnet_name = vnet_subnet['SubnetName']
                    
            #             if  ipaddress.ip_address(srcip) in ipaddress.ip_network(subnet_cidr):
            #                 maindf.at[index,'SrcVNet'] = vnet_name
            #                 maindf.at[index,'SrcSubnetName'] = subnet_name
            #                 maindf.at[index,'SrcName'] = 'unknown node in ' +  subnet_name
            #                 break
                    
            #     if destname == '':
            #         for index, vnet_subnet in vnets.iterrows():
            #             subnet_cidr = vnet_subnet['SubnetAddressPrefix']
            #             vnet_name = vnet_subnet['VNet']
            #             subnet_name = vnet_subnet['SubnetName']

            #             if ipaddress.ip_address(destip) in ipaddress.ip_network(subnet_cidr):
            #                 maindf.at[index,'DestVNet'] = vnet_name
            #                 maindf.at[index,'DestSubnetName'] = subnet_name
            #                 maindf.at[index,'DestName'] = 'unknown node in ' +  subnet_name
            #                 break


            maindf['SrcName'] = maindf.apply(lambda x: 'Unknown' if x['SrcName'] == '' else x['SrcName'], axis=1)
            maindf['SrcNodeType'] = maindf.apply(lambda x: 'UNKNOWN' if x['SrcName'] == 'Unknown' else x['SrcNodeType'], axis=1)

            maindf['DestName'] = maindf.apply(lambda x: 'Unknown' if x['DestName'] == '' else x['DestName'], axis=1)
            maindf['DestNodeType'] = maindf.apply(lambda x: 'UNKNOWN' if x['DestName'] == 'Unknown' else x['DestNodeType'], axis=1)

        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return maindf

    def _apply_filter_flow_direction(self, maindf: pd.DataFrame, flow_direction) -> pd.DataFrame:

        if flow_direction == 'all':
            return maindf
        
        return maindf[maindf['FlowDirection'] == flow_direction]     

    def _apply_filter_src_subscription(self, maindf: pd.DataFrame, subs: list[str]) -> pd.DataFrame:

        if not subs or len(subs) == 1 and subs[0] == 'all':
            return maindf
        
        return maindf[maindf['SrcSubscription'].isin(subs)]
        
        #return maindf[maindf['SrcSubscription'] == sub]
    
    def _apply_filter_src_rg(self, maindf: pd.DataFrame, rgs: list[str]) -> pd.DataFrame:

        if not rgs or len(rgs) == 1 and rgs[0] == 'all':
            return maindf
        
        rgs = [x.lower() for x in rgs]
        
        return maindf[maindf['SrcRG'].str.lower().isin(rgs)]
    
    def _apply_filter_dest_subscription(self, maindf: pd.DataFrame, subs) -> pd.DataFrame:

        if not subs or len(subs) == 1 and subs[0] == 'all':
            return maindf

        return maindf[maindf['DestSubscription'].isin(subs)]
    
    def _apply_filter_dest_rg(self, maindf: pd.DataFrame, rgs) -> pd.DataFrame:

        if not rgs or len(rgs) == 1 and rgs[0] == 'all':
            return maindf
        
        rgs = [x.lower() for x in rgs]
        
        return maindf[maindf['DestRG'].isin(rgs)]
    
    def _apply_filter_src_vnet(self, maindf: pd.DataFrame, src_vnets) -> pd.DataFrame:

        if not src_vnets or len(src_vnets) == 1 and src_vnets[0] == 'all':
            return maindf
        
        src_vnets = [x.lower() for x in src_vnets]
        
        return  maindf[maindf['SrcVNet'].isin(src_vnets)]
    
    def _apply_filter_src_subnet(self, maindf: pd.DataFrame, src_subnets) -> pd.DataFrame:

        if not src_subnets or len(src_subnets) == 1 and src_subnets[0] == 'all':
            return maindf
        
        src_subnets = [x.lower() for x in src_subnets]
        
        return  maindf[maindf['SrcSubnetName'].isin(src_subnets)]
        
    def _apply_filter_dest_vnet(self, maindf: pd.DataFrame, dest_vnets) -> pd.DataFrame:

        if not dest_vnets or len(dest_vnets) == 1 and dest_vnets[0] == 'all':
            return maindf
        
        dest_vnets = [x.lower() for x in dest_vnets]
        
        return  maindf[maindf['DestVNet'].isin(dest_vnets)]
        
    def _apply_filter_dest_subnet(self, maindf: pd.DataFrame, dest_subnets) -> pd.DataFrame:

        if not dest_subnets or len(dest_subnets) == 1 and dest_subnets[0] == 'all':
            return maindf
        
        dest_subnets = [x.lower() for x in dest_subnets]
        
        return  maindf[maindf['DestSubnetName'].isin(dest_subnets)]
        
    def _apply_filter_src_ip(self, maindf: pd.DataFrame, src_ips) -> pd.DataFrame:

        if not src_ips or len(src_ips) == 1 and src_ips[0] == 'all':
            return maindf
        
        return  maindf[maindf['SrcIp'].isin(src_ips)]
        
    def _apply_filter_dest_ip(self, maindf: pd.DataFrame, dest_ips) -> pd.DataFrame:

        if not dest_ips or len(dest_ips) == 1 and dest_ips[0] == 'all':
            return maindf
        
        return  maindf[maindf['DestIp'].isin(dest_ips)]
    
    def _apply_filter_estimated_duration_sec(self, maindf: pd.DataFrame, duration) -> pd.DataFrame:

        if not duration or len(duration) == 1 and duration[0] == -1:
            return maindf
        
        return  maindf[maindf['EstAvgDurationSec'].isin(duration)]
    
    def _apply_filter_src_payload_size(self, maindf: pd.DataFrame, size) -> pd.DataFrame:

        if not size or len(size) == 1 and size[0] == 'all':
            return maindf
        
        return  maindf[maindf['SrcToDestDataSize'].isin(size)]
    
    def _apply_filter_dest_payload_size(self, maindf: pd.DataFrame, size) -> pd.DataFrame:

        if not size or len(size) == 1 and size[0] == 'all':
            return maindf
        
        return  maindf[maindf['DestToSrcDataSize'].isin(size)]
    

    # def get_unique_src_subscription(self, current_data_key='') -> pd.DataFrame:

    #     global maindf_srcsub_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_srcsub_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}

    #     maindf = maindf.drop_duplicates(subset=['SrcIp', 'DestIp'], keep='first')
        
    #     tempdf = maindf.drop_duplicates('SrcSubscription', keep='first')
    #     tempdf = tempdf[tempdf['SrcSubscription'] != '']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf['SrcSubscription']

    #     maindf_srcsub_cache = {}

    #     return result.to_dict(orient='records')
    
    
    # def get_unique_src_rg(self, current_data_key='') -> pd.DataFrame:

    #     global maindf_srcrg_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_srcrg_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}
        
    #     tempdf = maindf.drop_duplicates('SrcRG', keep='first')
    #     tempdf = tempdf[tempdf['SrcRG'] != '']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf['SrcRG']

    #     maindf_srcrg_cache = {}
        
    #     return result.to_dict(orient='records')
    

    # def get_unique_src_vnet(self, current_data_key='') -> pd.DataFrame:
       
    #    global maindf_srcvnet_cache

    #    ok, maindf = self._get_maindf_from_cache_for_filter(maindf_srcvnet_cache, current_data_key)
    #    if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}
                    
    #    tempdf = maindf.drop_duplicates('SrcVNet', keep='first')
    #    tempdf = tempdf[tempdf['SrcVNet'] != '']

    #    result = pd.DataFrame()
    #    result['DisplayName'] = tempdf['SrcVNet']

    #    maindf_srcvnet_cache = {}
        
    #    return result.to_dict(orient='records')
    

    # def get_unique_src_subnet(self, current_data_key='') -> pd.DataFrame:

    #     global maindf_srcsubnet_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_srcsubnet_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}
        
    #     tempdf = pd.DataFrame()
    #     tempdf['SrcVNet'] = maindf['SrcVNet']
    #     tempdf['SrcSubnetName'] = maindf['SrcSubnetName'].str.lower()
    #     tempdf = tempdf.drop_duplicates('SrcSubnetName', keep='first')
    #     tempdf = tempdf[(tempdf['SrcVNet'] != '') & (tempdf['SrcSubnetName'] != '')]

    #     temp_result = pd.DataFrame()
    #     temp_result = tempdf[['SrcVNet', 'SrcSubnetName']]

    #     result = pd.DataFrame()
    #     result['DisplayName'] = temp_result.apply(lambda x: ' / '.join(x.dropna()), axis=1)
    #     result['SubnetName'] = temp_result['SrcSubnetName']

    #     maindf_srcsubnet_cache = {}
        
    #     return result.to_dict(orient='records')
    

    # def get_unique_src_ip(self, current_data_key='') -> pd.DataFrame:
        
    #     global maindf_srcip_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_srcip_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}
        
    #     maindf = maindf.drop_duplicates('SrcIp', keep='first')
    #     maindf= maindf[maindf['SrcIp'] != '']

    #     tempdf = pd.DataFrame()
    #     tempdf['SrcName '] = maindf['SrcName']
    #     tempdf['SrcIp'] = maindf['SrcIp']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf.apply(lambda x: ' / '.join(x.dropna()), axis=1)
    #     result['SrcIp'] = tempdf['SrcIp']

        
    #     maindf_srcip_cache = {}
        
    #     return result.to_dict(orient='records')
    
    # def get_unique_dest_subscription(self,current_data_key='') -> pd.DataFrame:

    #     global maindf_destsub_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_destsub_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}

    #     tempdf = pd.DataFrame()
    #     tempdf = maindf.drop_duplicates('DestSubscription', keep='first')
    #     tempdf = tempdf[tempdf['DestSubscription'] != '']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf['DestSubscription']

    #     maindf_destsub_cache = {}
        
    #     return result.to_dict(orient='records')

    # def get_unique_dest_rg(self, current_data_key='') -> pd.DataFrame:

    #     global maindf_destrg_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_destrg_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}
        
    #     tempdf = pd.DataFrame()
    #     tempdf = maindf.drop_duplicates('DestRG', keep='first')
    #     tempdf = tempdf[tempdf['DestRG'] != '']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf['DestRG']

    #     maindf_destrg_cache = {}
        
    #     return result.to_dict(orient='records')
    

    # def get_unique_dest_vnet(self, current_data_key='') -> pd.DataFrame:

    #     global maindf_destvnet_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_destvnet_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}

    #     tempdf = pd.DataFrame()
    #     tempdf = maindf.drop_duplicates('DestVNet', keep='first')
    #     tempdf = tempdf[tempdf['DestVNet'] != '']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf['DestVNet']

    #     maindf_destvnet_cache = {}
        
    #     return result.to_dict(orient='records')
    

    # def get_unique_dest_subnet(self, current_data_key='') -> pd.DataFrame:

    #     global maindf_destsubnet_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_destsubnet_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}

    #     tempdf = pd.DataFrame()
    #     tempdf['DestVNet'] = maindf['DestVNet']
    #     tempdf['DestSubnetName'] = maindf['DestSubnetName'].str.lower()
    #     tempdf = tempdf.drop_duplicates('DestSubnetName', keep='first')
    #     tempdf = tempdf[(tempdf['DestVNet'] != '') & (tempdf['DestSubnetName'] != '')]

    #     temp_result = pd.DataFrame()
    #     temp_result = tempdf[['DestVNet', 'DestSubnetName']]

    #     result = pd.DataFrame()
    #     result['DisplayName'] = temp_result.apply(lambda x: ' / '.join(x.dropna()), axis=1)
    #     result['SubnetName'] = temp_result['DestSubnetName']

    #     maindf_destsubnet_cache = {}
        
    #     return result.to_dict(orient='records')
    
    # def get_unique_dest_ip(self, current_data_key='') -> pd.DataFrame:
    #     '''
    #     wait_for_maindf is mainly for testing this function without having to call 
    #     '''
    #     global maindf_destip_cache

    #     ok, maindf = self._get_maindf_from_cache_for_filter(maindf_destip_cache, current_data_key)
    #     if not ok:
    #         return {'status': 'timeout as maindf took too long to complete'}

    #     # maindf = maindf.drop_duplicates(subset=['SrcIp', 'DestIp'], keep='first')
    #     maindf = maindf.drop_duplicates(subset=['SrcIp', 'DestIp'], keep='first')
        
    #     maindf = maindf.drop_duplicates('DestIp', keep='first')
    #     maindf= maindf[maindf['DestIp'] != '']

    #     tempdf = pd.DataFrame()
    #     tempdf['DestName '] = maindf['DestName']
    #     tempdf['DestIp'] = maindf['DestIp']

    #     result = pd.DataFrame()
    #     result['DisplayName'] = tempdf.apply(lambda x: ' / '.join(x.dropna()), axis=1)
    #     result['DestIp'] = tempdf['DestIp']

        
    #     maindf_destip_cache = {}
        
    #     return result.to_dict(orient='records')
    

    # # *** cache logic ***

    # def _set_maindf_cache(self, maindf: pd.DataFrame):
    #     global maindf_cache
    #     maindf_cache = maindf

    # def _get_maindf_cache(self, cache, current_data_key) -> list[bool,pd.DataFrame]:
        
    #     if current_data_key in cache:
    #         return True, cache[current_data_key]
            
    #     return False, pd.DataFrame()
    
    # def _get_maindf_from_cache_for_filter(self, cache = {}, current_data_key='') -> pd.DataFrame:
        
    #     # wait for get_network_map to complete fetching data and hydrating cache
    #     self._wait_for_maindf(cache, current_data_key)

    #     if current_data_key in cache:
    #         return True, cache[current_data_key]


    #     return False, pd.DataFrame()
        
        
    # def _wait_for_maindf(self, cache, current_data_key):
    #     '''
    #     a critical function used by "get filter data" functions to wait for maindf cache to be completed
    #     handles 2 scenario:
    #         - filter function started by network_map have not - (not maindf_in_progress and not maindf_completed
    #         - network_map started but filter function have not - (maindf_in_progress and not maindf_completed)
    #     '''
        
    #     wait_for = 0.5
    #     waited_sec = 0
    #     should_wait_until = filter_data_fetcher_wait_for_maindf_sec
        
    #     while current_data_key not in cache:
            
    #         # waited more than 7 secs, break out
    #         if waited_sec >= should_wait_until:
    #             break

    #         time.sleep(wait_for)
    #         waited_sec += wait_for
