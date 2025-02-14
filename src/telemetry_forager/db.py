from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError
from log import logger as Log
import logging
class DB:

    def __init__(self, config):
        self.config = config

        self.wara_run_history_table_name = 'WARARunHistory'
        self.wara_recommendation_table_name = 'WARARecommendation'
        self.wara_retirements_table_name = 'WARARetirements'
        self.wara_resource_type_table_name = 'WARAResourceType'
        self.wara_impacted_resources_table_name = 'WARAImpactedResources'
        self.wara_run_subscription_table_name = 'WARARunSubscription'

        self.table_service_client = TableServiceClient(endpoint=self.config.table_storage_url, 
                                                       credential=DefaultAzureCredential())
        

    def init(self):
        try:
            self.table_service_client.create_table_if_not_exists(table_name=self.wara_run_history_table_name)
            self.table_service_client.create_table_if_not_exists(table_name=self.wara_recommendation_table_name)
            self.table_service_client.create_table_if_not_exists(table_name=self.wara_retirements_table_name)
            self.table_service_client.create_table_if_not_exists(table_name=self.wara_resource_type_table_name)
            self.table_service_client.create_table_if_not_exists(table_name=self.wara_impacted_resources_table_name)
            self.table_service_client.create_table_if_not_exists(table_name=self.wara_run_subscription_table_name)
        except Exception as e:
            Log.exception(f'error occured: {str(e)}')
    

    def insert(self, table_name, entity):
        self.table_client = self.table_service_client.get_table_client(table_name=table_name)
        self.table_client.create_entity(entity=entity)

    def query(self, table_name, partition_key, row_key):
        try:
            self.table_client = self.table_service_client.get_table_client(table_name=table_name)
            return self.table_client.get_entity(partition_key, row_key)
        except ResourceNotFoundError as e:
            return None
        

    def get_all_rows(self, table_name):
        self.table_client = self.table_service_client.get_table_client(table_name=table_name)
        return self.table_client.list_entities()