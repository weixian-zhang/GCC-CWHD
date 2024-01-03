from enum import Enum
from abc import ABC, abstractclassmethod
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcehealth import ResourceHealthMgmtClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus, LogsQueryResult
from logging import Logger
from config import AppConfig, ResourceParameter
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from kql import KQL

class HealthReport:
    """
    A general data model used a a consistent return type for all health status result
    """
    # availabilityState
    # Available = 1, Unavailable = 0 or Unknown = 2
    # converting into number is easier to style by Grafana "threshold" 

    def __init__(self, 
                 location='', 
                 availabilityState='', 
                 summary='', 
                 reportedTime=None, 
                 stateLastChangeTime=None) -> None:

        self.location = location
        self.availabilityState = availabilityState
        self.summary = summary
        self.reportedTime = (reportedTime if not None else datetime.now())
        self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now())
        self.displayText = ''

        # if availabilityState == 'Available':
        #     self.availabilityState = 1
        #     self.displayText = 'Available'
        # elif availabilityState == 'Unavailable':
        #     self.availabilityState = 0
        #     self.displayText = 'Unavailable'
        # else:
        #     self.availabilityState = 2
        #     self.displayText = 'Unknown'




# strategy design pattern
class HealthStatusRetriever(ABC):
    @abstractclassmethod
    def get_health_status(self, resource: ResourceParameter):
        pass

    def query_monitor_log(self, query, timeSpan: timedelta) -> LogsQueryResult:

        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)

        response = client.query_workspace(
            workspace_id= self.appconfig.workspaceID,
            query=query,
            timespan=timeSpan
        )

        return response


class AppServiceHealthStatusRetriever(HealthStatusRetriever):
    """
    sample usage of LogQueryClient can be  found in the link
    https://github.com/Azure/azure-sdk-for-python/tree/azure-monitor-query_1.2.0/sdk/monitor/azure-monitor-query/samples
    """

    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig

    def get_health_status(self, resource):

        resourceId = resource.resourceId
        standardTestName = resource.standardTestName #self.appconfig.get_standardTestName_by_appsvc_rscId(resourceId)

        query = KQL.app_availability_result_query(standardTestName)

        #timeSpan does not matter as time filter is set in query
        self.logger.debug(f"""executing log query:
        {query}
        for resource Id {resourceId}
        """)
        
        response = super().query_monitor_log(query, timeSpan=timedelta(hours=2))
        
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            self.logger.error(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables

        if not data or not data[0].rows:
            self.logger.debug(f'no result found from log query AppServiceHealthStatusRetriever for resource Id: {resourceId}')
            return HealthReport(location= '',
                        availabilityState= 'Unavailable',
                        reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        singleRow = df.head(1)

        hr = HealthReport(location= singleRow['location'].values[0],
                        availabilityState= singleRow['availabilityState'].values[0],
                        reportedTime= pd.to_datetime(singleRow['reportedTime'].values[0])
        )
        
        return hr



class VMHealthStatusRetriever(HealthStatusRetriever):
    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig

    def query_cpu_usage_percenage(self, resourceId: str, queryTimeSpan: timedelta) -> int:
        cpuUsagePercentageQuery = KQL.cpu_usage_percentage_query(resourceId)

        #timeSpan does not matter as time filter is set in query
        self.logger.debug(f"""executing log query:
        {cpuUsagePercentageQuery}
        for resource Id {resourceId}
        """)
        
        cpuQueryResp = super().query_monitor_log(cpuUsagePercentageQuery, timeSpan=timedelta(hours=queryTimeSpan))

        if cpuQueryResp.status == LogsQueryStatus.PARTIAL:
            error = cpuQueryResp.partial_error
            data = cpuQueryResp.partial_data
            self.logger.error(error)
        elif cpuQueryResp.status == LogsQueryStatus.SUCCESS:
            data = cpuQueryResp.tables

        if not data or not data[0].rows:
            self.logger.debug(f'no result found from log query AppServiceHealthStatusRetriever for resource Id: {resourceId}')
            return HealthReport(location= '',
                        availabilityState= 'Unavailable',
                        reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        singleRow = df.head(1)

        return int(singleRow['CPUPercent'])
    

    def query_memory_usage_percenage(self, resourceId: str, queryTimeSpan: timedelta) -> int:

        memoryUsagePercentageQuery = KQL.memory_usage_percentage_query(resourceId)

        #timeSpan does not matter as time filter is set in query
        self.logger.debug(f"""executing log query:
        {memoryUsagePercentageQuery}
        for resource Id {resourceId}
        """)
        
        cpuQueryResp = super().query_monitor_log(memoryUsagePercentageQuery, timeSpan=timedelta(hours=queryTimeSpan))

        if cpuQueryResp.status == LogsQueryStatus.PARTIAL:
            error = cpuQueryResp.partial_error
            data = cpuQueryResp.partial_data
            self.logger.error(error)
        elif cpuQueryResp.status == LogsQueryStatus.SUCCESS:
            data = cpuQueryResp.tables

        if not data or not data[0].rows:
            self.logger.debug(f'no result found from log query AppServiceHealthStatusRetriever for resource Id: {resourceId}')
            return HealthReport(location= '',
                        availabilityState= 'Unavailable',
                        reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        singleRow = df.head(1)

        return int(singleRow['UsedMemoryPercentage'])
    

    def query_disk_usage_percenage(self, resourceId: str, queryTimeSpan: timedelta) -> dict:

        diskUsagePercentageQuery = KQL.disk_usage_percentage_query(resourceId, queryTimeSpan)

        #timeSpan does not matter as time filter is set in query
        self.logger.debug(f"""executing log query:
        {diskUsagePercentageQuery}
        for resource Id {resourceId}
        """)
        
        cpuQueryResp = super().query_monitor_log(diskUsagePercentageQuery, timeSpan=timedelta(hours=queryTimeSpan))

        if cpuQueryResp.status == LogsQueryStatus.PARTIAL:
            error = cpuQueryResp.partial_error
            data = cpuQueryResp.partial_data
            self.logger.error(error)
        elif cpuQueryResp.status == LogsQueryStatus.SUCCESS:
            data = cpuQueryResp.tables

        if not data or not data[0].rows:
            self.logger.debug(f'no result found from log query AppServiceHealthStatusRetriever for resource Id: {resourceId}')
            return HealthReport(location= '',
                        availabilityState= 'Unavailable',
                        reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)

        result = {}

        for _, row in df.iterrows():
            driveOrPath = row['Disk']
            usedSpacePercentage = row['UsedSpacePercentage']
            result[driveOrPath] = usedSpacePercentage


        return result


    def get_health_status(self, resource: ResourceParameter):

        queryTimeSpanHour = 1
        resourceId = resource.resourceId
        subscriptionId = resource.subscriptionId

        # scalar value
        cpuPercentage = self.query_cpu_usage_percenage(resourceId, queryTimeSpanHour)

        # scalar value
        usedMemoryPercentage = self.query_memory_usage_percenage(resourceId, queryTimeSpanHour)

        # dictionary of win drive/linux file path : used space percentage
        diskUsedPercentages = self.query_disk_usage_percenage(resourceId, queryTimeSpanHour)

        # resource health
        client = self._create_rh_client(subscriptionId)
        asResult = client.availability_statuses.get_by_resource(resource_uri=resourceId)
        availabilityStatus = asResult.properties.availability_state

        availabilityStateReportedTime = asResult.properties.reported_time
        availabilityState = 0
        if availabilityStatus == 'Available':
            availabilityState = 1

        # only if resource health availabilityState is 1 then consider metrics
        if availabilityState == 0:
            return HealthReport(location=asResult.location,
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
                self.logger.warn(f'CPU usage reaches threshold of {cpuThreshold}% for resource {resourceId}')
            elif usedMemoryPercentage >= memoryThreshold:
                availabilityState = 2
                self.logger.warn(f'Memory usage reaches threshold of {memoryThreshold}% for resource {resourceId}')
            else:
                diskUsagePercentages = list(diskUsedPercentages.values())
                if any(x >= diskThreshold for x in diskUsagePercentages):
                    availabilityState = 2
                    self.logger.warn(f'Disk usage reaches threshold of {diskThreshold}% for resource {resourceId}')

            return HealthReport(location=asResult.location,
                            availabilityState = availabilityState,
                            summary=asResult.properties.summary,
                            reportedTime=availabilityStateReportedTime)
        
        


class GeneralHealthStatusRetriever(HealthStatusRetriever):

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def get_health_status(self, resource: ResourceParameter):

        resourceId = resource.resourceId
        subscriptionId = resource.subscriptionId

        client = self._create_rh_client(subscriptionId)

        asResult = client.availability_statuses.get_by_resource(resource_uri=resourceId)

        availabilityState= 0
        if asResult.properties.availability_state == 'Available':
            availabilityState = 1
        elif asResult.properties.availability_state == 'Unknown':
            availabilityState = 2

        hr = HealthReport(location=asResult.location,
                            availabilityState=availabilityState,
                            summary=asResult.properties.summary,
                            reportedTime=asResult.properties.reported_time,
                            stateLastChangeTime=asResult.properties.occured_time)
        
        return hr

    def _create_rh_client(self, subscriptionId):
        return ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id = subscriptionId)

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

    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig
    
    def get_health(self, resource) -> HealthReport: #resourceId: str, subscriptionId: str) -> HealthReport:
        
        rscType =  self._get_resource_type(resource.resourceId)
        
        if rscType == AzResourceType.General:
            grc = GeneralHealthStatusRetriever(self.logger)
            hr = grc.get_health_status(resource) #resourceId=resourceId, subscriptionId=subscriptionId)
            return hr
        
        if rscType == AzResourceType.VM:
            client = VMHealthStatusRetriever(self.logger, self.appconfig)
            hr = client.get_health_status(resource)
            return hr
        
        if rscType == AzResourceType.AppService:
            client = AppServiceHealthStatusRetriever(self.logger, self.appconfig)
            hr = client.get_health_status(resource) #resourceId=resourceId,standardTestName=standardTestName)
            return hr
        

    def _get_resource_type(self, resourceId: str):
        if not resourceId:
            self.logger.debug('at HealthStatusClient.get_resource_type: resourceId cannot be empty')
            return
        
        rscIdSegments = resourceId.split('/')
        namespace = '/'.join(rscIdSegments[-3:-1])

        if namespace == 'Microsoft.Web/sites':  # app service
            return AzResourceType.AppService
        elif namespace == 'Microsoft.Compute/virtualMachines':
            return AzResourceType.VM
        else:
            return AzResourceType.General
        


        



