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


class Message:

    @staticmethod
    def params_not_exist():
        return 'Either resourceId, workspaceId or name of App Insights Standard Test is not found'
    

# strategy design pattern
class HealthStatusRetriever(ABC):

    @abstractclassmethod
    def get_health_status(self, resource: ResourceParameter):
        pass

    def query_monitor_log(self, workspaceId: str, query: str, timeSpan: timedelta) -> LogsQueryResult:

        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)

        response = client.query_workspace(
            workspace_id= workspaceId,
            query=query,
            timespan=timeSpan
        )

        return response


class AppServiceHealthStatusRetriever(HealthStatusRetriever):
    """
    sample usage of LogQueryClient can be  found in the link
    https://github.com/Azure/azure-sdk-for-python/tree/azure-monitor-query_1.2.0/sdk/monitor/azure-monitor-query/samples
    """


    def get_health_status(self, resource):

        workspaceId = resource.workspaceId
        resourceId = resource.resourceId
        standardTestName = resource.standardTestName

        if not resourceId or not standardTestName or not workspaceId:
            Log.warn(Message.params_not_exist())
            return HealthReport(
                        resourceId=resourceId,
                        description=Message.params_not_exist(),
                        availabilityState= 0,
                        reportedTime=datetime.now())

        query = KQL.app_availability_result_query(standardTestName)

        response = super().query_monitor_log(workspaceId=workspaceId, query=query, timeSpan=timedelta(hours=2))
        
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            Log.error(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables

        if not data or not data[0].rows:
            Log.warn(HealthReport.query_no_result_msg(), resourceId=resourceId)
            return HealthReport(
                        resourceId=resourceId,
                        description=HealthReport.query_no_result_msg(),
                        availabilityState= 0,
                        reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)

        availabilityState= int(df['availabilityState'].iat[0])
        reportedTime = df['reportedTime'].iat[0].strftime("%Y-%m-%dT%H:%M:%S")
        description = 'Resource is healthy' if availabilityState == 1 else 'Resource is unhealthy'

        hr = HealthReport(resourceId=resourceId,
                        description=description,
                        availabilityState= availabilityState,
                        reportedTime= reportedTime)
        
        return hr



class VMHealthStatusRetriever(HealthStatusRetriever):

    def __init__(self, appconfig: AppConfig) -> None:
        self.appconfig = appconfig


    def query_cpu_usage_percenage(self, resource: ResourceParameter, queryTimeSpan: timedelta) -> int:

        resourceId = resource.resourceId

        query = KQL.cpu_usage_percentage_query(resourceId)

        Log.debug(f"""executing log query:
        {query}
        for resource Id {resourceId}
        """)

        # timeSpan does not matter as time filter is set in query, but SDK requires it
        resp = super().query_monitor_log(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpan))

        if resp.status == LogsQueryStatus.PARTIAL:
            error = resp.partial_error
            data = resp.partial_data
            Log.exception(error, resourceId=resourceId)
        elif resp.status == LogsQueryStatus.SUCCESS:
            data = resp.tables

        # no result return, still consider available
        if not data or not data[0].rows:
            Log.warn(HealthReport.query_no_result_msg())
            return 0
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)

        usedCpuPercentage = int(df['CPUPercent'].iloc[0])

        return usedCpuPercentage
    

    def query_memory_usage_percenage(self, resource: ResourceParameter, queryTimeSpan: timedelta) -> int:

        resourceId = resource.resourceId

        query = KQL.memory_usage_percentage_query(resourceId)
        
        resp = super().query_monitor_log(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpan))

        if resp.status == LogsQueryStatus.PARTIAL:
            error = resp.partial_error
            data = resp.partial_data
            Log.exception(error, resourceId=resourceId)
        elif resp.status == LogsQueryStatus.SUCCESS:
            data = resp.tables

        # no result return, still consider available
        if not data or not data[0].rows:
            Log.warn(HealthReport.query_no_result_msg(), resourceId=resourceId)
            return 0
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        singleRow = df.head(1)
        usedMemoryPercentage = int(df['UsedMemoryPercentage'].iloc[0])

        return usedMemoryPercentage
    

    def query_disk_usage_percenage(self,  resource: ResourceParameter, queryTimeSpan: timedelta) -> dict:

        resourceId = resource.resourceId
        result = {}
        query = KQL.disk_usage_percentage_query(resourceId)
        
        resp = super().query_monitor_log(workspaceId=resource.workspaceId, query=query, timeSpan=timedelta(hours=queryTimeSpan))

        if resp.status == LogsQueryStatus.PARTIAL:
            error = resp.partial_error
            data = resp.partial_data
            Log.exception(error, resourceId=resourceId)
        elif resp.status == LogsQueryStatus.SUCCESS:
            data = resp.tables

        # no result return, still consider available
        if not data or not data[0].rows:
            Log.warn(HealthReport.query_no_result_msg(), resourceId=resourceId)
            return result

        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)

        for _, row in df.iterrows():
            driveOrPath = row['Disk']
            usedSpacePercentage = row['UsedSpacePercentage']
            result[driveOrPath] = usedSpacePercentage

        return result


    def get_health_status(self, resource: ResourceParameter):

        
        description = []
        queryTimeSpanHour = 2
        resourceId = resource.resourceId
        subscriptionId = resource.subscriptionId

        if not resourceId or not subscriptionId or not resource.workspaceId:
            
            Log.warn(f'Either resourceId, workspaceId or Subscription Id is not found')
            return HealthReport(
                    resourceId=resourceId,
                    description='Either resourceId, workspaceId or Subscription Id is not found',
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
                description.append(f'CPU usage reaches {cpuThreshold}% threshold')
                

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
                description = 'Resource is healthy'

            return HealthReport(resourceId=resourceId,
                                description=description,
                                availabilityState = availabilityState,
                                summary=asResult.properties.summary,
                                reportedTime=availabilityStateReportedTime)
        
        
class GeneralHealthStatusRetriever(HealthStatusRetriever):

    def get_health_status(self, resource: ResourceParameter):

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

class HealthStatusClient:
    """ The HealthStatusClient
    Main entry point to get resource health status for all resource types.
    Certain resource type like VM and App Service have additional factors that affects health status.
    Rest of resource health status are by default based on Azure Resource Health
    https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview 
    """

    def __init__(self, appconfig) -> None:
        self.appconfig = appconfig
    
    def get_health(self, resource: ResourceParameter) -> HealthReport:
        
        try:
            rscType =  self._get_resource_type(resource.resourceId)
            
            if rscType == AzResourceType.General:
                grc = GeneralHealthStatusRetriever()
                hr = grc.get_health_status(resource)
                return hr
            
            if rscType == AzResourceType.VM:
                client = VMHealthStatusRetriever(self.appconfig)
                hr = client.get_health_status(resource)
                return hr
            
            if rscType == AzResourceType.AppService:
                client = AppServiceHealthStatusRetriever()
                hr = client.get_health_status(resource)
                return hr
        
        except Exception as e:
            Log.exception(str(e), resouceId=resource.resourceId)
            return HealthReport(resourceId=resource.resourceId,
                                description='error occured at HealthStatusClient.get_health. Error is captured',
                                availabilityState=0)
        

    def _get_resource_type(self, resourceId: str):
        if not resourceId:
            self.logger.debug('at HealthStatusClient.get_resource_type: resourceId cannot be empty')
            return
        
        rscIdSegments = resourceId.split('/')
        namespace = '/'.join(rscIdSegments[-3:-1])

        if  namespace.lower() == 'Microsoft.Web/sites'.lower():  # app service
            return AzResourceType.AppService
        elif namespace.lower() == 'Microsoft.Compute/virtualMachines'.lower():
            return AzResourceType.VM
        else:
            return AzResourceType.General
        


        



