from db import DB
from config import AppConfig
from wara.model import WARAExecution, Subscription
import zlib
import json

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))

class WARAReport:
    def __init__(self, config: AppConfig):
        self.db = DB(config)

    def list_execution_history(self):
        entities = self.db.get_all_rows(self.db.run_history_table_name)
        executions = []
        for entity in entities:
            execution_id = entity['PartitionKey']
            execution_start_time = entity['execution_start_time']
            sub_ids = entity['subscription_ids'].split(',')
            executions.append(WARAExecution(execution_id, execution_start_time, sub_ids))
        
        return executions
    
    def get_run_subscriptions(self, execution_id):
        entity = self.db.query(self.db.run_subscription_table_name, partition_key=execution_id, row_key=execution_id)
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []

        return subscriptions

    def get_recommendations(self, subscription_id, execution_id):
        entity = self.db.query(self.db.recommendation_table_name, subscription_id, execution_id) 
        
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []
    
    def get_impacted_resources(self, subscription_id, execution_id):
        entity = self.db.query(self.db.impacted_resources_table_name, subscription_id, execution_id) 
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []
    
    def get_impacted_resource_types(self, subscription_id, execution_id):
        entity = self.db.query(self.db.resource_type_table_name, subscription_id, execution_id) 
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []
    

    def get_retirements(self, subscription_id, execution_id):
        entity = self.db.query(self.db.retirements_table_name, subscription_id, execution_id) 
        if entity and entity['data']:
            data = entity['data']
            data = self._decompress_string(data)
            return json.loads(data)
        return []


    def _decompress_string(self, data: str) -> str:
      data = zlib.decompress(data).decode()
      return data


 