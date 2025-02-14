from db import DB
from config import AppConfig
from wara.model import WARAExecution, Subscription
import zlib
import json
import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))

class WARAReport:
    def __init__(self, config: AppConfig):
        self.db = DB(config)

    def list_execution_history(self):
        entities = self.db.get_all_rows(self.db.wara_run_history_table_name)
        executions = []
        for entity in entities:
            execution_id = entity['PartitionKey']
            execution_start_time = entity['execution_start_time']
            executions.append(WARAExecution(execution_id, execution_start_time))
        
        return executions
    
    def get_run_subscriptions(self, execution_id):
        entity = self.db.query(self.db.wara_run_subscription_table_name, partition_key=execution_id, row_key=execution_id)
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []
    
    def get_pivot_recommendation_service_by_impact(self, subscription_id, execution_id):
        recommendations = self.get_recommendations(subscription_id, execution_id)

        df = pd.DataFrame(recommendations)

        pivot_by_service_df = df.pivot_table(index='ServiceTopic', columns="Impact", aggfunc='size', fill_value=0)

        return pivot_by_service_df.to_json()
    

    def get_pivot_recommendation_resiliency_by_impact(self, subscription_id, execution_id):
        recommendations = self.get_recommendations(subscription_id, execution_id)

        df = pd.DataFrame(recommendations)

        pivot_by_resiliency_cat_df = df.pivot_table(index='Resiliency_Category', columns="Impact", aggfunc='size', fill_value=0)

        return pivot_by_resiliency_cat_df.to_json()

    

    def get_recommendations(self, subscription_id, execution_id):
        entity = self.db.query(self.db.wara_recommendation_table_name, subscription_id, execution_id) 
        
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)
            df['Impact'] = df.iloc[:,8]
            df['Implemented'] = df.iloc[:,0]
            df['Number_of_Impacted_Resources'] = df.iloc[:,1]
            df['ResourceProvider'] = df.iloc[:,4]
            df['ServiceTopic'] = df.iloc[:,5]
            df['Resiliency_Category'] = df.iloc[:,6]
            df['Recommendation'] = df.iloc[:,7]
            df['Best_Practice_Guidance'] = df.iloc[:,9]
            df['Read_More'] = df.iloc[:,10]

            return df.to_json()
        
        return []
    
    def get_impacted_resources(self, subscription_id, execution_id):
        entity = self.db.query(self.db.wara_impacted_resources_table_name, subscription_id, execution_id) 
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)
            df['SubscriptionId'] = df.iloc[:,5]
            df['ResourceGroup'] = df.iloc[:,6]
            df['ResourceType'] = df.iloc[:,1]
            df['Name'] = df.iloc[:,8]
            df['Impact'] = df.iloc[:,4]
            df['Recommendation'] = df.iloc[:,2]
            df['Params'] = df.iloc[:,10].astype(str) + ', ' + df.iloc[:,11].astype(str) + ', ' + df.iloc[:,12].astype(str) + ', ' + df.iloc[:,13].astype(str) + ', ' + df.iloc[:,14].astype(str)
        
            return df.to_json()
        
        return []
    
    def get_impacted_resource_types(self, subscription_id, execution_id):
        entity = self.db.query(self.db.wara_resource_type_table_name, subscription_id, execution_id) 
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)
            df['ResourceType'] = df.iloc[:,0]
            df['NumberOfResources'] = df.iloc[:,1]
        
            return df.to_json()
        
        return []
    

    def get_retirements(self, subscription_id, execution_id):
        entity = self.db.query(self.db.wara_retirements_table_name, subscription_id, execution_id) 
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)
            df['SubscriptionId'] = df.iloc[:,0]
            df['Status'] = df.iloc[:,1]
            df['LastUpdateTime'] = df.iloc[:,3]
            df['EndTime'] = df.iloc[:,4]
            df['ImpactedService'] = df.iloc[:,5]
            df['Title'] = df.iloc[:,6]
            df['Details'] = df.iloc[:,8]
            df['RequiredAction'] = df.iloc[:,9]
        
            return df.to_json()
        
        return []


    def _decompress_string(self, data: str) -> str:
      data = zlib.decompress(data).decode()
      return data


 