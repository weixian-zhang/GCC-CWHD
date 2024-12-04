from enum import Enum
from abc import ABC, abstractclassmethod
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcehealth import ResourceHealthMgmtClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus, LogsQueryResult
from config import AppConfig, ResourceParameter
import pandas as pd
from datetime import datetime, timedelta
from kql import KQL
import log as Log
from model import HealthReport, ResourceParameter
import json

class Message:

    @staticmethod
    def params_not_exist():
        return 'Either resourceId, workspaceId or name of App Insights Standard Test is not found'
    

# strategy design pattern
class HealthRetriever(ABC):

    @abstractclassmethod
    def get_health_status(self, resource: ResourceParameter):
        pass

    def _kusto_query(self, workspaceId: str, query: str, timeSpan: timedelta) -> list[bool, pd.DataFrame]: # LogsQueryResult:

        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)

        response = client.query_workspace(
            workspace_id= workspaceId,
            query=query,
            timespan=timeSpan
        )

        if response.status != LogsQueryStatus.SUCCESS:
            Log.error(response.partial_error)
            return [False, pd.DataFrame()]
        
        if response.status == LogsQueryStatus.SUCCESS and response.tables and len(response.tables[0].rows) > 0:
            table = response.tables[0]
            df = pd.DataFrame(data=table.rows, columns=table.columns)
            return [True, df]

        return [False, pd.DataFrame()]
    
    def _get_health_report_by_resource_health(self,resourceId, subscriptionId) -> HealthReport:

        client = ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id = subscriptionId)

        asResult = client.availability_statuses.get_by_resource(resource_uri=resourceId)
        
        description = 'Resource is unhealthy'
        availabilityState= 0
        if asResult.properties.availability_state == 'Available':
            availabilityState = 1
            description = 'Resource is healthy'
        elif asResult.properties.availability_state == 'Unknown':
            availabilityState = 2
            description = 'Resource status is Unknown'

        hr = HealthReport(resourceId=resourceId,
                            description=description,
                            availabilityState=availabilityState,
                            reportedTime=asResult.properties.reported_time)
        
        return hr


class AppServiceHealthRetriever(HealthRetriever):
    """
    sample usage of LogQueryClient can be  found in the link
    https://github.com/Azure/azure-sdk-for-python/tree/azure-monitor-query_1.2.0/sdk/monitor/azure-monitor-query/samples
    """

    def __init__(self, appconfig) -> None:
        self.appconfig = appconfig


    def get_health_status(self, resource):
        '''
        AppServiceHealthRetriever gets health status from either one these ordered sources, if any one is successful, it uses that source.
            1. Azure Application Insights Availability Test
            2. Connection Monitor test result
            3. Resource Health
        '''

        with Log.get_tracer().start_as_current_span("log_query_app_insights_standard_test_result"):
            
            queryTimeSpanHour = self.appconfig.queryTimeSpanHour
            subscriptionId = resource.subscriptionId
            resourceId = resource.resourceId

            hr = HealthReport(resourceId=resourceId,
                                description='Resource is unhealthy or data not found',
                                availabilityState= 0,
                                reportedTime= datetime.now())
            

            # get health status from app insights availability test
            ok, hr = self._get_health_status_from_app_insights_availability_test(resource, queryTimeSpanHour)
            if ok:
                return hr
            

            ok, hr = self._get_health_status_from_connection_monitor_test(resource, queryTimeSpanHour)
            if ok:
                return hr
            
            hr = super()._get_health_report_by_resource_health(resourceId=resourceId, subscriptionId=subscriptionId)
            hr.description += ', status from Resource-Health'

            return hr
            
        
    def _get_health_status_from_app_insights_availability_test(
            self, resource: ResourceParameter, queryTimeSpanHour: int) -> list[bool, HealthReport]:
        
        resourceId = resource.resourceId
        workspaceId = resource.workspaceId
        standardTestName = resource.standardTestName

        if not workspaceId or not standardTestName:
            Log.warn(f'Either workspaceId or App Insights Availability Test name is not found')
            return [False, None]

        query = KQL.app_availability_result_query(standardTestName)

        ok, df = super()._kusto_query(workspaceId=workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpanHour))

        if ok:                        
            availabilityState= int(df['availabilityState'].iat[0])
            reportedTime = df['reportedTime'].iat[0].strftime("%Y-%m-%dT%H:%M:%S")
            description = 'Resource is healthy, status from App-Insights-Availability-Test' if availabilityState == 1 else 'Resource is unhealthy, , status from App-Insights-Availability-Test'

            hr = HealthReport(resourceId=resourceId,
                            description=description,
                            availabilityState= availabilityState,
                            reportedTime= reportedTime)
            
            return [True, hr]
        
        return [False, None]

    def _get_health_status_from_connection_monitor_test(
            self, resource: ResourceParameter, queryTimeSpanHour: int) -> list[bool, HealthReport]:
        
        resourceId = resource.resourceId
        workspaceId = resource.workspaceId
        network_watcher_conn_mon_test_group_name = resource.network_watcher_conn_mon_test_group_name

        if not workspaceId or not network_watcher_conn_mon_test_group_name:
            Log.warn(f'Either workspaceId or Network Watcher Connection Monitor name is not found')
            return [False, None]

        query = KQL.network_watcher_intranet_connection_monitor_http_test_query(network_watcher_conn_mon_test_group_name)

        ok, df = super()._kusto_query(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpanHour))

        if ok:                        
            availabilityState= int(df['availabilityState'].iat[0])
            reportedTime = df['reportedTime'].iat[0].strftime("%Y-%m-%dT%H:%M:%S")
            description = 'Resource is healthy, status from Network-Watcher-Conn-Monitor' if availabilityState == 1 else 'Resource is unhealthy, status from Network-Watcher-Conn-Monitor'

            hr = HealthReport(resourceId=resourceId,
                            description=description,
                            availabilityState= availabilityState,
                            reportedTime= reportedTime)
            
            return [True, hr]
        
        return [False, None]




class VMHealthRetriever(HealthRetriever):

    def __init__(self, appconfig: AppConfig) -> None:
        self.appconfig = appconfig


    def query_cpu_usage_percenage(self, resource: ResourceParameter, queryTimeSpan: timedelta) -> int:

        resourceId = resource.resourceId
        usedCpuPercentage = 0
        query = KQL.cpu_usage_percentage_query(resourceId)

        Log.debug(f"""executing log query:
        {query}
        for resource Id {resourceId}
        """)

        # timeSpan does not matter as time filter is set in query, but SDK requires it
        ok, df = super()._kusto_query(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpan))

        if ok:
            usedCpuPercentage = float(df['CPUPercent'].iloc[0])

        return usedCpuPercentage
    

    def query_memory_usage_percenage(self, resource: ResourceParameter, queryTimeSpan: timedelta) -> int:

        resourceId = resource.resourceId
        usedMemoryPercentage = 0
        query = KQL.memory_usage_percentage_query(resourceId)

        Log.debug(f"""executing log query:
        {query}
        for resource Id {resourceId}
        """)

        ok, df = super()._kusto_query(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpan))


        if ok:
            usedMemoryPercentage = int(df['UsedMemoryPercentage'].iloc[0])

        return usedMemoryPercentage
    

    def query_disk_usage_percenage(self,  resource: ResourceParameter, queryTimeSpan: timedelta) -> dict:

        resourceId = resource.resourceId
        result = {}
        query = KQL.disk_usage_percentage_query(resourceId)

        Log.debug(f"""executing log query:
        {query}
        for resource Id {resourceId}
        """)
        
        ok, df = super()._kusto_query(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpan))


        if ok:
            for _, row in df.iterrows():
                driveOrPath = row['Disk']
                usedSpacePercentage = row['UsedSpacePercentage']
                result[driveOrPath] = usedSpacePercentage

        return result


    def get_health_status(self, resource: ResourceParameter):

        description = []
        queryTimeSpanHour = self.appconfig.queryTimeSpanHour
        resourceId = resource.resourceId
        subscriptionId = resource.subscriptionId

        if not resourceId or not subscriptionId or not resource.workspaceId:
            
            Log.warn(f'Either resourceId, workspaceId or name of App Insights Standard Test is not found')
            return HealthReport(
                    resourceId=resourceId,
                    description='Either resourceId or workspaceId is not found',
                    availabilityState= 0,
                    reportedTime=datetime.now())

        tracer = Log.get_tracer()
        with tracer.start_as_current_span("vm_health_status"):
            
            with tracer.start_as_current_span('retrieve_cpu_metric'):
                # scalar value
                cpuPercentage = self.query_cpu_usage_percenage(resource, queryTimeSpanHour)

            with tracer.start_as_current_span('retrieve_memory_metric'):
                # scalar value
                usedMemoryPercentage = self.query_memory_usage_percenage(resource, queryTimeSpanHour)

            with tracer.start_as_current_span('retrieve_disk_drives_metrics'):
                # result contains dictionary of win drive/linux file path : used space percentage
                diskUsedPercentages = self.query_disk_usage_percenage(resource, queryTimeSpanHour)
        

        # resource health
        rhClient = ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id = subscriptionId)
        asResult = rhClient.availability_statuses.get_by_resource(resource_uri=resourceId)
        availabilityStatus = asResult.properties.availability_state

        availabilityStateReportedTime = asResult.properties.reported_time
        availabilityState = 0
        if availabilityStatus == 'Available':
            availabilityState = 1

        # only if resource health availabilityState is 1 then consider metrics
        if availabilityState == 0:
            return HealthReport(resourceId=resourceId,
                                description=f'Resource is unhealthy reported by Azure Resource Health',
                            availabilityState = 0,
                            summary=asResult.properties.summary,
                            reportedTime=availabilityStateReportedTime)
        else:
            cpuThreshold = self.appconfig.health_status_threshold.VM.cpuUsagePercentage
            memoryThreshold = self.appconfig.health_status_threshold.VM.memoryUsagePercentage
            diskThreshold = self.appconfig.health_status_threshold.VM.diskUsagePercentage

            # any metric hits threshold is warning, availabilityState = 2
            if cpuPercentage >= cpuThreshold:
                availabilityState = 2
                description.append(f'CPU % reaches {cpuThreshold}% threshold')
                
            if usedMemoryPercentage >= memoryThreshold:
                availabilityState = 2
                description.append(f'Memory usage reaches {memoryThreshold}% threshold')

            diskUsagePercentages = list(diskUsedPercentages.values())
            if any(x >= diskThreshold for x in diskUsagePercentages):
                availabilityState = 2
                description.append(f'One or more disk usage reaches {diskThreshold}% threshold')
                Log.warn(description)

            if len(description) >= 1:
                description = ', '.join(description)
                Log.warn(description)
            else:
                description = f'''Resource is healthy
                 - CPU: {cpuPercentage}%
                 - Memory: {usedMemoryPercentage}%
                 - Disk: {json.dumps(diskUsedPercentages)}
                '''

            return HealthReport(resourceId=resourceId,
                                description=description,
                                availabilityState = availabilityState,
                                summary=asResult.properties.summary,
                                reportedTime=availabilityStateReportedTime)
        
        
class GeneralHealthRetriever(HealthRetriever):

    def get_health_status(self, resource: ResourceParameter):

        with Log.get_tracer().start_as_current_span("get_resource_health_availability_status"):

            resourceId = resource.resourceId
            subscriptionId = resource.subscriptionId

            client = ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id = subscriptionId)

            asResult = client.availability_statuses.get_by_resource(resource_uri=resourceId)
            
            description = 'Resource is unhealthy'
            availabilityState= 0
            if asResult.properties.availability_state == 'Available':
                availabilityState = 1
                description = 'Resource is healthy'
            elif asResult.properties.availability_state == 'Unknown':
                availabilityState = 2
                description = 'Resource status is Unknowny'

            hr = HealthReport(resourceId=resourceId,
                                description=description,
                                availabilityState=availabilityState,
                                reportedTime=asResult.properties.reported_time)
            
            return hr

class AzResourceType(Enum):
    VM = 1
    AppService = 2
    General = 3

class HealthClient:
    """ The HealthClient
    Main entry point to get resource health status for all resource types.
    Certain resource type like VM and App Service have additional factors that affects ":"color coded" health status.
    Rest of resource health status are by default based on Azure Resource Health
    https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview 
    """

    def __init__(self, appconfig) -> None:
        self.appconfig = appconfig
        self.ghc = GeneralHealthRetriever()
        self.vmhr = VMHealthRetriever(self.appconfig)
        self.appsvchr = AppServiceHealthRetriever(self.appconfig)
    
    def get_health(self, resource: ResourceParameter) -> HealthReport:
        
        try:
            rscType =  self._get_resource_type(resource.resourceId)
            
            if rscType == AzResourceType.General:
                #grc = GeneralHealthRetriever()
                hr = self.ghc.get_health_status(resource)
                return hr
            
            if rscType == AzResourceType.VM:
                #client = VMHealthRetriever(self.appconfig)
                hr = self.vmhr.get_health_status(resource) # client.get_health_status(resource)
                return hr
            
            if rscType == AzResourceType.AppService:
                #client = AppServiceHealthRetriever()
                hr = self.appsvchr.get_health_status(resource) #client.get_health_status(resource)
                return hr
        
        except Exception as e:
            Log.exception(str(e), resouceId=resource.resourceId)
            return HealthReport(resourceId=resource.resourceId,
                                description='error occured at HealthClient.get_health. Error is captured',
                                availabilityState=0)
        

    def _get_resource_type(self, resourceId: str):
        if not resourceId:
            self.logger.debug('at HealthClient.get_resource_type: resourceId cannot be empty')
            return
        
        rscIdSegments = resourceId.split('/')
        namespace = '/'.join(rscIdSegments[-3:-1])

        if  namespace.lower() == 'Microsoft.Web/sites'.lower():  # app service
            return AzResourceType.AppService
        elif namespace.lower() == 'Microsoft.Compute/virtualMachines'.lower():
            return AzResourceType.VM
        else:
            return AzResourceType.General
        


        



