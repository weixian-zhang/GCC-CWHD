from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError

class DB:

    def __init__(self, config):
        self.config = config

        self.run_history_table_name = 'RunHistory'
        self.recommendation_table_name = 'Recommendation'
        self.retirements_table_name = 'Retirements'
        self.resource_type_table_name = 'ResourceType'
        self.impacted_resources_table_name = 'ImpactedResources'
        self.run_subscription_table_name = 'RunSubscription'

        self.table_service_client = TableServiceClient(endpoint=self.config.table_storage_url, credential=DefaultAzureCredential())
        

    def init(self):
        self.table_service_client.create_table_if_not_exists(table_name=self.run_history_table_name)
        self.table_service_client.create_table_if_not_exists(table_name=self.recommendation_table_name)
        self.table_service_client.create_table_if_not_exists(table_name=self.retirements_table_name)
        self.table_service_client.create_table_if_not_exists(table_name=self.resource_type_table_name)
        self.table_service_client.create_table_if_not_exists(table_name=self.impacted_resources_table_name)
        self.table_service_client.create_table_if_not_exists(table_name=self.run_subscription_table_name)

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