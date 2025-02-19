from db import DB
from config import AppConfig
from wara.model import WARAExecution, Subscription
import zlib
import json
import pandas as pd
import sys
import log as Log
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))

class WARAReport:
    def __init__(self, config: AppConfig):
        self.db = DB(config)

    def list_execution_history(self):

     
        entities = self.db.get_all_rows(self.db.wara_run_history_table_name)
        executions = []
        for entity in entities:
            rowkey = entity['RowKey']
            execution_id = entity['PartitionKey']
            execution_start_time = entity['execution_start_time']
            display_execution_start_time = entity['display_execution_start_time']
            executions.append(WARAExecution(rowkey, execution_id, execution_start_time, display_execution_start_time))

        executions = sorted(executions, key=lambda x: x.rowkey)
        
        return executions
        
        
    
    def get_run_subscriptions(self, execution_id):

        entity = self.db.get_row(self.db.wara_run_subscription_table_name, partition_key=execution_id, row_key=execution_id)
        
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []
        
    
    def get_pivot_recommendation_service_by_impact(self, subscription_id, execution_id):

        df = self.get_recommendations(subscription_id, execution_id, to_df=True)

        if df is []:
            return []
        
        pivot_Table = df.pivot_table(index='ServiceTopic', columns="Impact", aggfunc='size', fill_value=0)

        pdf = pivot_Table.reset_index() # convert pivot to dataframe

        return pdf.to_json(orient="records")
        
    
    def get_pivot_recommendation_resiliency_by_impact(self, subscription_id, execution_id):
        
        df = self.get_recommendations(subscription_id, execution_id, to_df=True)

        if df is []:
            return []

        pivot_Table = df.pivot_table(index='Resiliency_Category', columns="Impact", aggfunc='size', fill_value=0)

        pdf = pivot_Table.reset_index() # convert pivot to dataframe

        return pdf.to_json(orient="records")
    

    def get_recommendations(self, subscription_id, execution_id, to_df=False):
        '''
        Get recommendations for a given subscription and execution id
        params:
            to_df (bool): if True, return a pandas dataframe, else return a json string
        '''

        entity = self.db.get_row(self.db.wara_recommendation_table_name, subscription_id, execution_id) 
        
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)

            newdf = pd.DataFrame()
            newdf['Impact'] = df.iloc[:,8]
            newdf['Implemented'] = df.iloc[:,0]
            newdf['Number_of_Impacted_Resources'] = df.iloc[:,1]
            newdf['ResourceProvider'] = df.iloc[:,4]
            newdf['ServiceTopic'] = df.iloc[:,5]
            newdf['Resiliency_Category'] = df.iloc[:,6]
            newdf['Recommendation'] = df.iloc[:,7]
            newdf['Best_Practice_Guidance'] = df.iloc[:,9]
            newdf['Read_More'] = df.iloc[:,10]

            if not to_df:
                return newdf.to_json(orient='records')
            else:
                return newdf 
        
        return []
    
    
    def get_impacted_resources(self, subscription_id, execution_id):

        entity = self.db.get_row(self.db.wara_impacted_resources_table_name, subscription_id, execution_id) 

        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)

            newdf = pd.DataFrame()
            #newdf['SubscriptionId'] = df.iloc[:,5]
            newdf['ResourceGroup'] = df.iloc[:,6]
            newdf['ResourceType'] = df.iloc[:,1]
            newdf['Name'] = df.iloc[:,8]
            newdf['Impact'] = df.iloc[:,4]
            newdf['Recommendation'] = df.iloc[:,2]
            newdf['Params'] = df.iloc[:,10].astype(str) + ', ' + df.iloc[:,11].astype(str) + ', ' + df.iloc[:,12].astype(str) + ', ' + df.iloc[:,13].astype(str) + ', ' + df.iloc[:,14].astype(str)
        
            return newdf.to_json(orient='records')
        
        return []
        
    
    def get_impacted_resource_types(self, subscription_id, execution_id):


        entity = self.db.get_row(self.db.wara_resource_type_table_name, subscription_id, execution_id) 

        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)

            newdf = pd.DataFrame()
            newdf['ResourceType'] = df.iloc[:,0]
            newdf['NumberOfResources'] = df.iloc[:,1]
        
            return newdf.to_json(orient='records')
        
        return []
    

    def get_retirements(self, subscription_id, execution_id):

        entity = self.db.get_row(self.db.wara_retirements_table_name, subscription_id, execution_id) 

        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)

            newdf = pd.DataFrame()
            #newdf['SubscriptionId'] = df.iloc[:,0]
            newdf['Status'] = df.iloc[:,1]
            newdf['LastUpdateTime'] = df.iloc[:,3]
            newdf['EndTime'] = df.iloc[:,4]
            newdf['ImpactedService'] = df.iloc[:,5]
            newdf['Title'] = df.iloc[:,6]
            newdf['Details'] = df.iloc[:,8]
            newdf['RequiredAction'] = df.iloc[:,9]
        
            return newdf.to_json(orient='records')
        
        return []


    def _decompress_string(self, data: str) -> str:
      data = zlib.decompress(data).decode()
      return data


 