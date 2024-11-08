from typing import List
from fastapi import FastAPI, Response
from pydantic import BaseModel
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

app = FastAPI()

# load environment variables
appconfig = AppConfig()
# load env vars
appconfig.load_from_envar()

Log.init(appconfig)

class RequestResourceListParam(BaseModel):
    resourceId: str
    standardTestName: str | None = None
    workspaceId: str | None = None

class RequestBodyParam(BaseModel):
    resources: List[RequestResourceListParam]

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


def _get_subscription_id(resourceId: str) -> str:
    if not resourceId:
        return ''
    if resourceId[0] == '/':
        resourceId = resourceId[1:]
    return resourceId.split('/')[1]

    
def get_resource_params(rbp: RequestBodyParam) -> list[ResourceParameter]:
    if not rbp or not rbp.resources:
        return []
    
    resource_params = rbp.resources

    exist = set()
    result = []

    for r in resource_params:
        resourceId = r.resourceId.lower() if r.resourceId else ''

        if resourceId in exist:
            continue
        
        exist.add(resourceId)

        subscriptionId = _get_subscription_id(resourceId)
        standardTestName = r.standardTestName if r.standardTestName else ''
        workspaceId = r.workspaceId if r.workspaceId else ''

        result.append(ResourceParameter(
            resourceId,
            subscriptionId,
             standardTestName,
             workspaceId
            ))
        
    return result

def get_resource_health_states(resources: List[ResourceParameter]) -> RHResult:

    if not resources:
        return []
    
    healthStatuses = []
    
    for rsc in resources:

        client = HealthStatusClient(appconfig)

        healthReport = client.get_health(rsc)

        healthStatuses.append(healthReport)

    return RHResult(healthStatuses)



app = FastAPI()

@app.get("/", status_code=200)
def root():
    return "alive"

@app.post("/RHRetriever", status_code=200)
def RHRetriever(req_body_param: RequestBodyParam, response: Response):

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
        
        tracer = Log.get_tracer()

        with tracer.start_as_current_span("main_request_RHRetriever", kind=SpanKind.SERVER):

            resource_params = get_resource_params(req_body_param)

            if not RHRetriever:
                Log.exception('no resource ID supplied')
                response.status_code = 400
                return 'no resource ID supplied'

            rhState = get_resource_health_states(resource_params)

            return jsons.dumps(rhState)

    except Exception as e:
        Log.exception(f'error occured: {str(e)}')
        response.status_code = 500
        return str(e)
