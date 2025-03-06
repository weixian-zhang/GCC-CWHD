from db import DB
from config import AppConfig
from wara.model import WARAExecution, Subscription
import zlib
import json
import pandas as pd
import sys
import log as Log
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).absolute().parent))

from util import DatetimeUtil

class WARAApi:
    def __init__(self, config: AppConfig):
        self.db = DB(config)

    def list_execution_history(self):

     
        entities = self.db.get_all_rows(self.db.wara_run_history_table_name)
        executions = []
        for entity in entities:
            rowkey = entity['RowKey']
            execution_id = entity['PartitionKey']
            edt = entity['execution_start_time'] # TablesEntityDatetime type need to convert to datetime
            execution_start_time = datetime(edt.year, edt.month, edt.day, edt.hour, edt.minute, edt.second, tzinfo=edt.tzinfo)
            display_execution_start_time = DatetimeUtil.to_friendly_datetime(execution_start_time) #entity['display_execution_start_time']
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
        
    
    def get_pivot_resources_by_impact(self, subscription_id, execution_id):

        df = self.get_impacted_resources(subscription_id, execution_id, to_df=True)

        if df is []:
            return []
        
        
        pivot_Table = df.pivot_table(index='ResourceType', columns="Impact", aggfunc='size', fill_value=0)

        pdf = pivot_Table.reset_index() # convert pivot to dataframe

        return pdf.to_json(orient="records")
        
    
    def get_pivot_resiliency_by_impact(self, subscription_id, execution_id):
        
        df = self.get_recommendations(subscription_id, execution_id, to_df=True)

        if df is []:
            return []

        pivot_Table = df.pivot_table(index='Resiliency_Category', columns="Impact", aggfunc='size', fill_value=0)

        pdf = pivot_Table.reset_index() # convert pivot to dataframe

        return pdf.to_json(orient="records")
    

    def get_recommendations(self, subscription_id, execution_id, implemented='All', impact='All', resource_provider='All', to_df=False):
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
            newdf['ResourceProviderCategory'] = df.iloc[:,4]
            newdf['ResourceProvideType'] = df.iloc[:,5]
            newdf['ResourceProvider'] = newdf['ResourceProviderCategory'] + '/' + newdf['ResourceProvideType']
            newdf['Resiliency_Category'] = df.iloc[:,6]
            newdf['Recommendation'] = df.iloc[:,7]
            newdf['Best_Practice_Guidance'] = df.iloc[:,9]
            newdf['Read_More'] = df.iloc[:,10]

            # filter after column rename
            newdf = newdf[newdf['Implemented'].str.lower() == implemented.lower()] if implemented != 'All' else newdf
            newdf = newdf[newdf['Impact'].str.lower() == impact.lower()] if impact != 'All' else newdf
            newdf = newdf[newdf['ResourceProvider'].str.lower() == resource_provider.lower()] if resource_provider != 'All' else newdf

            if not to_df:
                return newdf.to_json(orient='records')
            else:
                return newdf 
        
        return []
    
    
    def get_impacted_resources(self, subscription_id, execution_id, impact='All',resource_provider='All', to_df=False):

        entity = self.db.get_row(self.db.wara_impacted_resources_table_name, subscription_id, execution_id) 

        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            jd = json.loads(data)

            df = pd.DataFrame(jd)

            newdf = pd.DataFrame()
            #newdf['SubscriptionId'] = df.iloc[:,5]
            newdf['ResourceGroup'] = df.iloc[:,6]
            newdf['ResourceProvider'] = df.iloc[:,1]
            newdf['Name'] = df.iloc[:,8]
            newdf['Impact'] = df.iloc[:,4]
            newdf['Recommendation'] = df.iloc[:,2]
            newdf['Params'] = df.iloc[:,10].astype(str) + ', ' + df.iloc[:,11].astype(str) + ', ' + df.iloc[:,12].astype(str) + ', ' + df.iloc[:,13].astype(str) + ', ' + df.iloc[:,14].astype(str)

            newdf = newdf[newdf['Impact'].str.lower() == impact.lower()] if impact != 'All' else newdf
            newdf = newdf[newdf['ResourceProvider'].str.lower() == resource_provider.lower()] if resource_provider != 'All' else newdf

            if not to_df:
                return newdf.to_json(orient='records')
            else:
                return newdf 
        
        return []
        
    
    def get_impacted_resource_count(self, subscription_id, execution_id, impact='All', resource_provider='All'):

        df = self.get_impacted_resources(subscription_id, execution_id, impact, resource_provider, to_df=True)

        df = df[df['Impact'].str.lower() == impact.lower()] if impact != 'All' else df

        df = df.groupby(['ResourceProvider']).size().reset_index(name='counts')
        
        return df.to_json(orient='records')
    

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


 