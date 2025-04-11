import azure.functions as func
from healthstatus import HealthStatusClient, HealthReport
import jsons
from datetime import datetime
from config import AppConfig
from model import ResourceParameter
import log as Log
from opentelemetry.trace import (
    SpanKind
)
from opentelemetry.propagate import extract

# load environment variables
appconfig = AppConfig()
# load env vars
appconfig.load_from_envar()

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

        self.set_overall_health_state()

    def set_overall_health_state(self):

        if not self.states:
            return
        
        if all([x.availabilityState == 1 for x in self.states]):
            self.overallHealth = 1
            self.overallSummary = 'Available'
            return
        
        if any([x.availabilityState == 0 for x in self.states]):
            self.overallHealth = 0
            self.overallSummary = 'Unavailable'
            return
        
        if any([x.availabilityState == 2 for x in self.states]):
            self.overallHealth = 2
            self.overallSummary = 'Warning'

def get_resources(reqBody) -> list[ResourceParameter]:
    if not reqBody:
        return []
    
    result = []
    rscs = reqBody['resources']

    if not rscs:
        raise Exception('"resources" Json parameter is missing in HTTP POST Body')

    for r in rscs:
        resourceId = r['resourceId']
        resourceId = resourceId[1:] if resourceId[0] == '/' else resourceId
        subscriptionId = resourceId.split('/')[1]
        standardTestName = r['standardTestName'] if 'standardTestName' in r else ''
        workspaceId = r['workspaceId'] if 'workspaceId' in r else appconfig.workspaceId

        result.append(ResourceParameter(
                resourceId,
                subscriptionId,
                standardTestName,
                workspaceId
            ))
        
        
    return result


def get_resource_health_states(resources: list[ResourceParameter]) -> RHResult:

    if not resources:
        return []
    
    healthStatuses = []
    
    for rsc in resources:

        client = HealthStatusClient(appconfig)

        healthReport = client.get_health(rsc)

        healthStatuses.append(healthReport)

    return RHResult(healthStatuses)



app = func.FunctionApp()

@app.route(route="RHRetriever", methods=("POST", "GET"), auth_level=func.AuthLevel.FUNCTION)
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
        # supports alive ping
        if req.method == "GET":
            return func.HttpResponse('ALIVE', status_code=200)

        Log.init(appconfig)

        tracer = Log.get_tracer()

        with tracer.start_as_current_span("main_request_RHRetriever",context=extract(req.headers), kind=SpanKind.SERVER):
        
            resources = get_resources(req.get_json())

            if not resources:
                Log.exception('no resource ID supplied')
                return func.HttpResponse('no resource ID supplied', status_code=400)

            rhState = get_resource_health_states(resources)

            return func.HttpResponse(
                                    jsons.dumps(rhState),
                                    status_code=200)
        
            

    except Exception as e:
        Log.exception(f'error occured: {str(e)}')
        return func.HttpResponse(str(e), status_code=500)


