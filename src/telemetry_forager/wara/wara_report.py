import sys
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))
from db import DB
from config import AppConfig
from model import WARAExecution
import zlib
import json


class WARAReport:
    def __init__(self, config: AppConfig):
        self.db = DB(config)

    def list_executions(self):
        entities = self.db.get_all_rows(self.db.run_history_table_name)
        executions = []
        for entity in entities:
            execution_id = entity['PartitionKey']
            execution_start_time = entity['execution_start_time']
            sub_ids = entity['subscription_ids'].split(',')
            executions.append(WARAExecution(execution_id, execution_start_time, sub_ids))
        
        return executions
    

    def get_recommendations(self, subscription_id, execution_id):
        entity = self.db.query(self.db.recommendation_table_name, subscription_id, execution_id) 
        data = entity['data']
        if data:
            data = self._decompress_string(data)
            return json.loads(data)
        return None


    def _decompress_string(self, data: str) -> str:
      data = zlib.decompress(data).decode()
      return data


 