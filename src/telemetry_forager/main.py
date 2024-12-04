from typing import List
from fastapi import FastAPI, Response
import uvicorn
from pydantic import BaseModel
from health import HealthStatusClient
import jsons
from datetime import datetime
from config import AppConfig
from model import ResourceParameter, ResourceHealthResult
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

def get_resource_health_states(resources: List[ResourceParameter]) -> ResourceHealthResult:

    if not resources:
        return []
    
    healthStatuses = []
    
    for rsc in resources:

        client = HealthStatusClient(appconfig)

        healthReport = client.get_health(rsc)

        healthStatuses.append(healthReport)

    return ResourceHealthResult(healthStatuses)



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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)