from enum import Enum
from abc import ABC, abstractclassmethod
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcehealth import ResourceHealthMgmtClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from logging import Logger
from config import AppConfig
import pandas as pd

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
        self.reportedTime = (reportedTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
        self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
        self.displayText = ''

        if availabilityState == 'Available':
            self.availabilityState = 1
            self.displayText = 'Available'
        elif availabilityState == 'Unavailable':
            self.availabilityState = 0
            self.displayText = 'Unavailable'
        else:
            self.availabilityState = 2
            self.displayText = 'Unknown'

class HealthStatusStrategy(ABC):
    @abstractclassmethod
    def get_health_status(self, resourceId: str):
        pass

class AppServiceHealthStatus(HealthStatusStrategy):

    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig

    def get_health_status(self, resourceId: str):

        try:

            standardTestName = self.appconfig.appServiceAppInsightStandardTestMap[resourceId]

            query = f"""AppAvailabilityResults
                    | where Name == '{standardTestName}'
                    | extend availabilityState = iif(Success == true, 'Available', 'Unavailable')
                    | order by TimeGenerated desc 
                    | take 1
                    | project ['reportedTime']=TimeGenerated, ['location']=Location, ['Name']=Name, availabilityState
                    """

            credential = DefaultAzureCredential()
            client = LogsQueryClient(credential)

            response = client.query_workspace(
                workspace_id= self.appconfig.workspaceID,
                query=query
            )

            if response.status == LogsQueryStatus.PARTIAL:
                error = response.partial_error
                data = response.partial_data
                self.logger.debug(error)
            elif response.status == LogsQueryStatus.SUCCESS:
                data = response.tables

            #for table in data:
            df = pd.DataFrame(data)
            singleRow = df.head(1)

            hr = HealthReport(location= singleRow['location'],
                            availabilityState= singleRow['availabilityState'],
                            reportedTime=singleRow['reportedTime'])
            
            return hr

        except Exception as e:
            self.logger.debug(e)

# for future enhancements
class VMHealthStatus:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def get_health_status(self, resourceId: str):
        pass


class GeneralHealthStatus:

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def get_health_status(self, resourceId: str, subscriptionId: str):
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
    Rest of resource health statusare by default based on Azure Resource Health
    https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview 
    """

    def __init__(self, logger: Logger, appconfig: AppConfig) -> None:
        self.logger = logger
        self.appconfig = appconfig
    
    def get_health(self, resourceId: str, subscriptionId: str) -> HealthReport:
        
        rscType =  self._get_resource_type(resourceId)
        
        if rscType == AzResourceType.General:
            grc = GeneralHealthStatus()
            hr = grc.get_health_status(resourceId=resourceId, subscriptionId=subscriptionId)
            return hr
        
        if rscType == AzResourceType.AppService:
            pass
            return
        
        if rscType == AzResourceType.VM:
            pass


    def _get_resource_type(self, resourceId: str):
        if not resourceId:
            self.logger.debug('at HealthStatusClient.get_resource_type: resourceId cannot be empty')
            return
        
        rscIdSegments = resourceId.split('/')

        # app service
        if rscIdSegments[-3:-1] == 'Microsoft.Web/sites':
            return AzResourceType.AppService
        # elif rscIdSegments[-3:-1] == 'Microsoft.Compute/virtualMachines':
        #     return AzResourceType.VM
        else:
            return AzResourceType.General


#         /subscriptions/ee611083-4581-4ba1-8116-a502d4539206/resourceGroups/rg-azworkbench-dev/providers/Microsoft.Web/sites/portal-azworkbench-dev
# /subscriptions/ee611083-4581-4ba1-8116-a502d4539206/resourceGroups/rggccshol/providers/Microsoft.Compute/virtualMachines/addns

        



