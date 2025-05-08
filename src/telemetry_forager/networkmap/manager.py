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
from .model import NetworkMapResult
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import *
import ipaddress
import json

maindf_cache = pd.DataFrame

class NetworkMapManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.kql = NetworkMapKQL()
        self.azcred = DefaultAzureCredential()
        self.law_client = LogsQueryClient(self.azcred )
        self.rg_client = ResourceGraphClient(credential=self.azcred)

        # start_time = datetime.now(timezone.utc) - timedelta(days=1)
        # end_time = datetime.now(timezone.utc)
        # flow_types: []
        # flow_direction: str = 'all',
        # src_subscrition: str = 'all',
        # dest_subscription: str = 'all',
        # src_rg: str = 'all',
        # dest_rg: str = 'all',
        # src_vnet: str = 'all',
        # dest_vnet: str = 'all',
        # src_subnet: str = 'all',
        # dest_subnet: str = 'all',
        # src_ip: str = 'all',
        # dest_ip: str = 'all'


    def _set_maindf_cache(self, maindf: pd.DataFrame):
        global maindf_cache
        maindf_cache = maindf

    def _get_maindf_cache(self,start_time, end_time, flow_types) -> pd.DataFrame:
        
        if maindf_cache.empty:
            kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)
            maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
            self._set_maindf_cache(maindf)
        
        return maindf_cache
        

    def get_network_map_without_externalpublic_malicious(self, 
                               start_time: datetime, 
                               end_time: datetime,
                               flow_types: list[str] = [],
                               flow_direction: str = 'all',
                               src_subscrition: str = 'all',
                               dest_subscription: str = 'all',
                               src_rg: str = 'all',
                               dest_rg: str = 'all',
                               src_vnet: str = 'all',
                               dest_vnet: str = 'all',
                               src_subnet: str = 'all',
                               dest_subnet: str = 'all',
                               src_ip: str = 'all',
                               dest_ip: str = 'all') -> NetworkMapResult:
        
        try:

            kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

            maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)

            if maindf.empty:
                return {}
        
            self._resolve_src_dest_name_for_known_traffic(maindf)

            maindf = self._apply_filter_flow_direction(maindf, flow_direction)

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

            nodes = self._create_echart_nodes(maindf=maindf)

            edges = self._create_echart_edges(maindf=maindf)

            categories = self._create_echart_categories(maindf=maindf)

            #cache maindf for filter data use
            self._set_maindf_cache(maindf)

            nmap = NetworkMapResult(nodes, edges, categories)

            return nmap


        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}

    def _create_echart_nodes(self, maindf: pd.DataFrame) -> dict:

        src_nodes_final_df = pd.DataFrame()
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


        # # #id,title,subtitle,mainstat,secondarystat,color
        combined_list = [src_nodes_final_df, dest_nodes_final_df]

        final_nodes_df = pd.concat(combined_list)

        final_nodes_df = final_nodes_df.drop_duplicates(subset=['id'])

        final_nodes_json_str =  final_nodes_df.to_json(orient='records')

        result = json.loads(final_nodes_json_str)

        return result
    
    def _create_echart_edges(self, maindf: pd.DataFrame) -> dict:

        edges_df = pd.DataFrame()
        edges_df['source'] = maindf['SrcIp']
        edges_df['target'] = maindf['DestIp']
        # edges_df['value'] = tempdf['SrcToDestDataSize'] + '-> <-' + tempdf['DestToSrcDataSize'] + '<div> flowtype: ' + tempdf['FlowType'] + '</div>' + '<div> protocol: ' +  tempdf['protocol'] + '/div>'
        edges_df['src_to_dest_data_size'] = maindf['SrcToDestDataSize']
        edges_df['dest_to_srct_data_size'] = maindf['DestToSrcDataSize']
        edges_df['flowType'] = maindf['FlowType']
        edges_df['flowDirection'] = maindf['FlowDirection']
        edges_df['flowEncryption'] = maindf['FlowEncryption']
        edges_df['protocol'] = maindf['protocol']
        edges_df['connectionType'] = maindf['ConnectionType']

        edges_df = edges_df.drop_duplicates(subset=['source', 'target'])

        final_edges_json_str =  edges_df.to_json(orient='records')

        result = json.loads(final_edges_json_str)

        return result   

    def _create_echart_categories(self, maindf: pd.DataFrame) -> dict:
        tempdf = pd.DataFrame()
        tempdf['name'] = maindf['FlowType'].unique()
        result =  tempdf.to_json(orient='records')
        return result
    

    def _get_main_dataframe(self, kql_query, start_time, end_time) -> pd.DataFrame:

        try:

            df = self._get_vnet_flow_log(kql_query=kql_query, start_time=start_time, end_time=end_time)

            # update SrcName with Subnet name if SrcName is empty        
            df['SrcName'] = df.apply(lambda x: x['SrcSubnetName'] if x['SrcName']=='' else x['SrcName'], axis=1)

            maindf = df.drop_duplicates(subset=['SrcName', 'DestName'])

            maindf.fillna('', inplace=True)

            return maindf

        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}


    def _get_vnet_flow_log(self, kql_query, start_time, end_time) -> pd.DataFrame:

        try:

            df = pd.DataFrame()

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
        

    def _resolve_src_dest_name_for_known_traffic(self, maindf: pd.DataFrame):
        """
        Resolve the source and destination names for known traffic.
        *in-place update of maindf
        """

        try:

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
            vnet_subnet_names = pd.DataFrame(data_row, columns=data_cols)


            # resolve vnet name and subnet name in maind from existing vnets
            unknownprivate_df = maindf[(maindf['FlowType'] == 'UnknownPrivate') | (maindf['FlowType'] == 'Unknown')]

            for index, ukprow in unknownprivate_df.iterrows():
                srcip = ukprow['SrcIp']
                destip = ukprow['DestIp']

                for index, vnet_subnet in vnet_subnet_names.iterrows():
                    subnet_cid = vnet_subnet['SubnetAddressPrefix']
                    
                    try:

                        if ipaddress.ip_address(srcip) in ipaddress.ip_network(subnet_cid):
                            unknownprivate_df['SrcVNet'] = vnet_subnet['VNet']
                            unknownprivate_df['SrcSubnetName'] = vnet_subnet['SubnetName']
                            unknownprivate_df['SrcName'] = 'vm in ' +  unknownprivate_df["SrcSubnetName"]

                        if ipaddress.ip_address(destip) in ipaddress.ip_network(subnet_cid):
                            unknownprivate_df['DestName'] = vnet_subnet['VNet']
                            unknownprivate_df['DestSubnetName'] = vnet_subnet['SubnetName']
                            unknownprivate_df['DestName'] = 'vm in ' +  unknownprivate_df["SrcSubnetName"]

                    except Exception as e:
                        continue

            maindf.update(unknownprivate_df)

        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return maindf

    def _apply_filter_flow_direction(self, maindf: pd.DataFrame, flow_direction) -> pd.DataFrame:

        if flow_direction == 'all':
            return maindf
        
        return maindf[maindf['FlowDirection'] == flow_direction]     

    def _apply_filter_src_subscription(self, maindf: pd.DataFrame, sub) -> pd.DataFrame:

        if sub == 'all':
            return maindf
        
        return maindf[maindf['SrcSubscription'] == sub]
    
    def _apply_filter_src_rg(self, maindf: pd.DataFrame, rg) -> pd.DataFrame:

        if rg == 'all':
            return maindf
        
        return maindf[maindf['SrcRG'].str.lower() == rg.lower()]
    

    def _apply_filter_dest_subscription(self, maindf: pd.DataFrame, sub) -> pd.DataFrame:

        if sub == 'all':
            return maindf
        
        return maindf[maindf['DestSubscription'] == sub]
    
    def _apply_filter_dest_rg(self, maindf: pd.DataFrame, rg) -> pd.DataFrame:

        if rg == 'all':
            return maindf
        
        return maindf[maindf['DestRG'].str.lower() == rg.lower()]
    
    
    def _apply_filter_src_vnet(self, maindf: pd.DataFrame, src_vnet) -> pd.DataFrame:

        if src_vnet == 'all':
            return maindf
        
        return maindf[maindf['SrcVNet'].str.lower() == src_vnet.lower()]
    
    def _apply_filter_src_subnet(self, maindf: pd.DataFrame, src_subnet) -> pd.DataFrame:

        if src_subnet == 'all':
            return maindf
        
        return maindf[maindf['SrcSubnetName'].str.lower() == src_subnet.lower()]
    
    def _apply_filter_dest_vnet(self, maindf: pd.DataFrame, dest_vnet) -> pd.DataFrame:

        if dest_vnet == 'all':
            return maindf
        
        return maindf[maindf['DestVNet'].str.lower() == dest_vnet.lower()]
    
    def _apply_filter_dest_subnet(self, maindf: pd.DataFrame, dest_subnet) -> pd.DataFrame:

        if dest_subnet == 'all':
            return maindf
        
        return maindf[maindf['DestSubnetName'].str.lower() == dest_subnet.lower()]
    
    def _apply_filter_src_ip(self, maindf: pd.DataFrame, src_ip) -> pd.DataFrame:

        if src_ip == 'all':
            return maindf
        
        return maindf[maindf['SrcIp'] == src_ip]
    
    def _apply_filter_dest_ip(self, maindf: pd.DataFrame, dest_ip) -> pd.DataFrame:

        if dest_ip == 'all':
            return maindf
        
        return maindf[maindf['DestIp'] == dest_ip]
    

    def get_unique_src_subscription(self,flow_types,start_time, end_time) -> pd.DataFrame:

        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)
        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
        
        tempdf = maindf.drop_duplicates('SrcSubscription', keep='first')
        tempdf = tempdf[tempdf['SrcSubscription'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['SrcSubscription']

        result.loc[-1] = ['all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        

        return result.to_dict(orient='records')
    
    
    def get_unique_src_rg(self,flow_types,start_time, end_time) -> pd.DataFrame:

        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)
        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
        
        tempdf = maindf.drop_duplicates('SrcRG', keep='first')
        tempdf = tempdf[tempdf['SrcRG'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['SrcRG']

        result.loc[-1] = ['all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    

    def get_unique_src_vnet(self,flow_types,start_time, end_time) -> pd.DataFrame:

        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
                    
        tempdf = maindf.drop_duplicates('SrcVNet', keep='first')
        tempdf = tempdf[tempdf['SrcVNet'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['SrcVNet']

        result.loc[-1] = ['all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    

    def get_unique_src_subnet(self, flow_types,start_time, end_time) -> pd.DataFrame:

        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        
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

        result.loc[-1] = ['all', 'all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    

    def get_unique_src_ip(self, flow_types,start_time, end_time) -> pd.DataFrame:
                    
        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)

        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
        
        maindf = maindf.drop_duplicates('SrcIp', keep='first')
        maindf= maindf[maindf['SrcIp'] != '']

        tempdf = pd.DataFrame()
        tempdf['SrcName '] = maindf['SrcName']
        tempdf['SrcIp'] = maindf['SrcIp']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf.apply(lambda x: ' / '.join(x.dropna()), axis=1)
        result['SubnetName'] = tempdf['SrcIp']

        result.loc[-1] = ['all', 'all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    
    def get_unique_dest_subscription(self,flow_types,start_time, end_time) -> pd.DataFrame:

        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('DestSubscription', keep='first')
        tempdf = tempdf[tempdf['DestSubscription'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['DestSubscription']

        result.loc[-1] = ['all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')

    def get_unique_dest_rg(self,flow_types,start_time, end_time) -> pd.DataFrame:

        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
        
        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('DestRG', keep='first')
        tempdf = tempdf[tempdf['DestRG'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['DestRG']

        result.loc[-1] = ['all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    

    def get_unique_dest_vnet(self, flow_types,start_time, end_time) -> pd.DataFrame:
        
        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)

        tempdf = pd.DataFrame()
        tempdf = maindf.drop_duplicates('DestVNet', keep='first')
        tempdf = tempdf[tempdf['DestVNet'] != '']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf['DestVNet']

        result.loc[-1] = ['all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    

    def get_unique_dest_subnet(self, flow_types,start_time, end_time) -> pd.DataFrame:
                    
        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)

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

        result.loc[-1] = ['all', 'all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')
    
    def get_unique_dest_ip(self, flow_types,start_time, end_time) -> pd.DataFrame:
                    
        # kql_query = self.kql.vnet_flow_without_externalpublic_malicious_query(flow_types=flow_types)

        # maindf = self._get_main_dataframe(kql_query, start_time=start_time, end_time=end_time)
        maindf = self._get_maindf_cache(start_time, end_time, flow_types)
        
        maindf = maindf.drop_duplicates('DestIp', keep='first')
        maindf= maindf[maindf['DestIp'] != '']

        tempdf = pd.DataFrame()
        tempdf['DestName '] = maindf['DestName']
        tempdf['DestIp'] = maindf['DestIp']

        result = pd.DataFrame()
        result['DisplayName'] = tempdf.apply(lambda x: ' / '.join(x.dropna()), axis=1)
        result['SubnetName'] = tempdf['DestIp']

        result.loc[-1] = ['all', 'all']  # adding a row
        result.index = result.index + 1  # shifting index
        result.sort_index(inplace=True) 
        result.reset_index(drop=True)  # reset index
        
        return result.to_dict(orient='records')