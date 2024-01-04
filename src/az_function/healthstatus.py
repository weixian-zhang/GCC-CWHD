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
                 resourceId='',
                 description='', 
                 availabilityState='', 
                 summary='', 
                 reportedTime=None, 
                 stateLastChangeTime=None) -> None:
        
        self.availabilityState = availabilityState
        self.resourceId = resourceId
        self.description = description
        self.reportedTime = (reportedTime if not None else datetime.now())

        #self.location = location    # obsolete, to be deleted
        self.summary = summary      # obsolete, to be deleted
        self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now())    # obsolete, to be deleted
        self.displayText = '' # obsolete, to be deleted
        

        # if availabilityState == 'Available':
        #     self.availabilityState = 1
        #     self.displayText = 'Available'
        # elif availabilityState == 'Unavailable':
        #     self.availabilityState = 0
        #     self.displayText = 'Unavailable'
        # else:
        #     self.availabilityState = 2
        #     self.displayText = 'Unknown'

    @staticmethod
    def query_no_result_msg(resourceId: str):
        return f'health status log or metric result not found for resource {resourceId}'



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
            self.logger.warn(HealthReport.query_no_result_msg(resourceId))
            return HealthReport(
                        resourceId=resourceId,
                        description=HealthReport.query_no_result_msg(resourceId),
                        availabilityState= 0,
                        reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        singleRow = df.head(1)

        availabilityState= singleRow['availabilityState'].values[0]
        description = 'Resource is healthy' if availabilityState == 1 else 'Resource is unhealthy'

        hr = HealthReport(resourceId=resourceId,
                          description=description,
                        availabilityState= availabilityState,
                        reportedTime= pd.to_datetime(singleRow['reportedTime'].values[0])
        )
        
        return hr



class VMHealthStatusRetriever(HealthStatusRetriever):

    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig

    def query_cpu_usage_percenage(self, resourceId: str, queryTimeSpan: timedelta) -> int:

        cpuUsagePercentageQuery = KQL.cpu_usage_percentage_query(resourceId)

        self.logger.debug(f"""executing log query:
        {cpuUsagePercentageQuery}
        for resource Id {resourceId}
        """)

        # timeSpan does not matter as time filter is set in query, but SDK requires it
        resp = super().query_monitor_log(cpuUsagePercentageQuery, timeSpan=timedelta(hours=queryTimeSpan))

        if resp.status == LogsQueryStatus.PARTIAL:
            error = resp.partial_error
            data = resp.partial_data
            self.logger.error(error)
        elif resp.status == LogsQueryStatus.SUCCESS:
            data = resp.tables

        # no result return, still consider available
        if not data or not data[0].rows:
            self.logger.warn(HealthReport.query_no_result_msg(resourceId))
            return 0
            # return HealthReport(resourceId=resourceId,
            #                     description=HealthReport.query_no_result_msg(resourceId),
            #             availabilityState= 1,
            #             reportedTime=datetime.now())
        
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
        
        resp = super().query_monitor_log(memoryUsagePercentageQuery, timeSpan=timedelta(hours=queryTimeSpan))

        if resp.status == LogsQueryStatus.PARTIAL:
            error = resp.partial_error
            data = resp.partial_data
            self.logger.error(error)
        elif resp.status == LogsQueryStatus.SUCCESS:
            data = resp.tables

        # no result return, still consider available
        if not data or not data[0].rows:
            self.logger.warn(f'no result found from log query VMHealthStatusRetriever for resource Id: {resourceId}')
            return 0
            # return HealthReport(resourceId=resourceId,
            #             description=HealthReport.query_no_result_msg(resourceId),
            #             availabilityState= 1,
            #             reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        singleRow = df.head(1)

        return int(singleRow['UsedMemoryPercentage'])
    

    def query_disk_usage_percenage(self, resourceId: str, queryTimeSpan: timedelta) -> dict:

        result = {}
        diskUsagePercentageQuery = KQL.disk_usage_percentage_query(resourceId)

        #timeSpan does not matter as time filter is set in query
        self.logger.debug(f"""executing log query:
        {diskUsagePercentageQuery}
        for resource Id {resourceId}
        """)
        
        resp = super().query_monitor_log(diskUsagePercentageQuery, timeSpan=timedelta(hours=queryTimeSpan))

        if resp.status == LogsQueryStatus.PARTIAL:
            error = resp.partial_error
            data = resp.partial_data
            self.logger.error(error)
        elif resp.status == LogsQueryStatus.SUCCESS:
            data = resp.tables

        # no result return, still consider available
        if not data or not data[0].rows:
            self.logger.warn(description=HealthReport.query_no_result_msg(resourceId))
            return result
            # return HealthReport(resourceId=resourceId,
            #                     description=HealthReport.query_no_result_msg(resourceId),
            #                     availabilityState= 1,
            #                     reportedTime=datetime.now())
        
        # parse query result
        table = data[0]
        df = pd.DataFrame(data=table.rows, columns=table.columns)

        

        for _, row in df.iterrows():
            driveOrPath = row['Disk']
            usedSpacePercentage = row['UsedSpacePercentage']
            result[driveOrPath] = usedSpacePercentage

        return result


    def get_health_status(self, resource: ResourceParameter):

        description = 'Resource is healthy'
        queryTimeSpanHour = 2
        resourceId = resource.resourceId
        subscriptionId = resource.subscriptionId

        # scalar value
        cpuPercentage = self.query_cpu_usage_percenage(resourceId, queryTimeSpanHour)

        # scalar value
        usedMemoryPercentage = self.query_memory_usage_percenage(resourceId, queryTimeSpanHour)

        # dictionary of win drive/linux file path : used space percentage
        diskUsedPercentages = self.query_disk_usage_percenage(resourceId, queryTimeSpanHour)

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
                                description=f'Resource is unhealthy reported from Resource Health for resource {resourceId}',
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
                description = f'CPU usage reaches {cpuThreshold}% threshold for resource {resourceId}'
                self.logger.warn(description)
            elif usedMemoryPercentage >= memoryThreshold:
                availabilityState = 2
                description = f'Memory usage reaches {memoryThreshold}% threshold for resource {resourceId}'
                self.logger.warn(description)
            else:
                diskUsagePercentages = list(diskUsedPercentages.values())
                if any(x >= diskThreshold for x in diskUsagePercentages):
                    availabilityState = 2
                    description = f'One or more disk usage reaches {diskThreshold}% threshold for resource {resourceId}'
                    self.logger.warn(description)

            return HealthReport(resourceId=resourceId,
                                description=description,
                                availabilityState = availabilityState,
                                summary=asResult.properties.summary,
                                reportedTime=availabilityStateReportedTime)
        
        


class GeneralHealthStatusRetriever(HealthStatusRetriever):

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

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

    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig
    
    def get_health(self, resource) -> HealthReport:
        
        rscType =  self._get_resource_type(resource.resourceId)
        
        if rscType == AzResourceType.General:
            grc = GeneralHealthStatusRetriever(self.logger)
            hr = grc.get_health_status(resource)
            return hr
        
        if rscType == AzResourceType.VM:
            client = VMHealthStatusRetriever(self.logger, self.appconfig)
            hr = client.get_health_status(resource)
            return hr
        
        if rscType == AzResourceType.AppService:
            client = AppServiceHealthStatusRetriever(self.logger, self.appconfig)
            hr = client.get_health_status(resource)
            return hr
        

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
        


        



