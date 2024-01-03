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
        # self.reportedTime = (reportedTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
        # self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
        # self.displayText = ''

        if availabilityState == 'Available':
            self.availabilityState = 1
            self.displayText = 'Available'
        elif availabilityState == 'Unavailable':
            self.availabilityState = 0
            self.displayText = 'Unavailable'
        else:
            self.availabilityState = 2
            self.displayText = 'Unknown'




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

# decorator design pattern
# for future enhancement to health status influence by additional metrics and log result
# class HealthStatusInfluencer(HealthStatusRetriever):
#     def __init__(self, HealthStatusRetriever) -> None:
#         self.HealthStatusRetriever = HealthStatusRetriever

#     @abstractclassmethod
#     def get_health_status(self, resourceId: str):
#         pass


class AppServiceHealthStatus(HealthStatusRetriever):
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

        query = f"""AppAvailabilityResults 
        | where Name == '{standardTestName}' 
        | where TimeGenerated >= ago(2h) 
        | extend availabilityState = iif(Success == true, 'Available', 'Unavailable') 
        | order by TimeGenerated desc 
        | take 1 
        | project ['reportedTime']=TimeGenerated, ['location']=Location, ['Name']=Name, availabilityState"""

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
            self.logger.debug(f'no result found from log query AppServiceHealthStatus for resource Id: {resourceId}')
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



# for future enhancement
# class VMHealthStatus:
#     def __init__(self, logger: Logger) -> None:
#         self.logger = logger

#     def get_health_status(self, resourceId: str):
#         pass


class GeneralHealthStatus:

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def get_health_status(self, resource: ResourceParameter):

        resourceId = resource.resourceId
        subscriptionId = resource.subscriptionId

        client = self._create_rh_client(subscriptionId)

        asResult = client.availability_statuses.get_by_resource(resource_uri=resourceId)

        hr = HealthReport(location=asResult.location,
                            availabilityState=asResult.properties.availability_state,
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
        
        #resourceId = resource.resourceId
        # subscriptionId = resource.subscriptionId

        rscType =  self._get_resource_type(resource.resourceId)
        
        if rscType == AzResourceType.General:
            grc = GeneralHealthStatus(self.logger)
            hr = grc.get_health_status(resource) #resourceId=resourceId, subscriptionId=subscriptionId)
            return hr
        
        if rscType == AzResourceType.AppService:
            client = AppServiceHealthStatus(self.logger, self.appconfig)
            hr = client.get_health_status(resource) #resourceId=resourceId,standardTestName=standardTestName)
            return hr
        
        # if rscType == AzResourceType.VM:
        #     pass


    def _get_resource_type(self, resourceId: str):
        if not resourceId:
            self.logger.debug('at HealthStatusClient.get_resource_type: resourceId cannot be empty')
            return
        
        rscIdSegments = resourceId.split('/')
        namespace = '/'.join(rscIdSegments[-3:-1])

        if namespace == 'Microsoft.Web/sites':  # app service
            return AzResourceType.AppService
        else:
            return AzResourceType.General
        


        



