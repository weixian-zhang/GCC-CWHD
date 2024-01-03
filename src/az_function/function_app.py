import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcehealth import ResourceHealthMgmtClient
from healthstatus import HealthStatusClient, HealthReport
import logging
from datetime import datetime
import jsons
from config import AppConfig, ResourceParameter
import jsonpickle

#override Azure's root logger to be able to log to console
logger = logging.getLogger('akshay')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

# load environment variables
appconfig = AppConfig()

class ResourceHealthAPIResult:

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


class RHResult:
    def __init__(self, states: list[HealthReport]) -> None: #list[ResourceHealthAPIResult]) -> None:

        # overallHealth
        # Available = 1, Unavailable = 0, Partial = 2
        # converting into number is easier to style by Grafana "threshold"

        self.overallHealth = 1
        self.overallSummary = ''

        self.states: list[HealthReport] = states

        self.set_overall_state()

    def set_overall_state(self):

        if not self.states:
            return
        
        if all([x.availabilityState == 1 for x in self.states]):
            self.overallHealth = 1
            self.overallSummary = 'Available'
        else:
            self.overallHealth = 0
            self.overallSummary = 'Unavailable'

def get_resources(reqBody) -> list[ResourceParameter]:
    if not reqBody:
        return []
    
    result = []
    rscs = reqBody['resources']

    for r in rscs:
        standardTestName = r['standardTestName'] if 'standardTestName' in r else ''
        result.append(ResourceParameter(
            r['resourceId'],
             r['subscriptionId'],
             standardTestName,
            ))
        
    return result

def create_rh_client(subscriptionId):
    return ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id = subscriptionId)

def get_resource_health_states(resources: list[ResourceParameter]) -> RHResult:

    if not resources:
        return []
    
    healthStatuses = []
    
    for rsc in resources:

        logger.debug(f'retrieving availability status for resource {rsc.resourceId}')

        client = HealthStatusClient(logger, appconfig)

        healthReport = client.get_health(rsc)

        logger.debug(f'availability status retrieved successfully for resource {rsc.resourceId}')
        
        healthStatuses.append(healthReport)

    return RHResult(healthStatuses)



app = func.FunctionApp()

@app.route(route="RHRetriever", auth_level=func.AuthLevel.FUNCTION)
def RHRetriever(req: func.HttpRequest) -> func.HttpResponse:

    """
    azure.identity.DefaultAzureCredential in Azure uses managed identity.
    on local machine, requires 4 environment variables:
        AZURE_SUBSCRIPTION_ID,
        AZURE_CLIENT_ID,
        AZURE_CLIENT_SECRET,
        AZURE_TENANT_ID,

    environment variables:
        WorkspaceID
        AppServiceAppInsightStandardTestMap
    """
    
    try:
        

        logger.debug('request received')

        # load env vars
        appconfig.load_from_envar()

        resources = get_resources(req.get_json())

        if not resources:
            logger.debug('no resource ID supplied')
            return func.HttpResponse('no resource ID supplied', status_code=400)

        rhState = get_resource_health_states(resources)
        
        logger.debug('request completed, returning result')

        return func.HttpResponse(
                                jsons.dumps(rhState),
                                status_code=200)

    except Exception as e:
        logger.error(f'error occured: {str(e)}')
        return func.HttpResponse(str(e), status_code=500)
