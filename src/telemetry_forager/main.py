from typing import List
import fastapi #import FastAPI, Response
import uvicorn
from pydantic import BaseModel
from health import HealthClient
import jsons
from config import AppConfig
from model import ResourceParameter, ResourceHealthResult
import log as Log
from wara.action_plan import WARAActionPlanner
from opentelemetry.trace import (
    SpanKind
)

from opentelemetry.propagate import extract

# load environment variables
appconfig = AppConfig()
# load env vars
appconfig.load_from_envar()

Log.init(appconfig)

app = fastapi.FastAPI()

class RequestResourceListParam(BaseModel):
    resourceId: str
    workspaceId: str | None = None
    standardTestName: str | None = None
    network_watcher_conn_mon_test_group_name: str | None = None

class RequestBodyParam(BaseModel):
    resources: List[RequestResourceListParam]


def _get_subscription_id(resourceId: str) -> str:
    if not resourceId:
        return ''
    if resourceId[0] == '/':
        resourceId = resourceId[1:]
    return resourceId.split('/')[1]

    
def get_resource_params(rbp: RequestBodyParam) -> list[bool, list[ResourceParameter]]:
    if not rbp or not rbp.resources:
        return []
    
    resource_params = rbp.resources

    exist = set()
    result = []

    for r in resource_params:
        resourceId = r.resourceId.lower() if r.resourceId else ''

        if resourceId == '':
            return [False, []]

        if resourceId in exist:
            continue
        
        exist.add(resourceId)

        subscriptionId = _get_subscription_id(resourceId)
        standardTestName = r.standardTestName if r.standardTestName else ''
        network_watcher_conn_mon_test_group_name = r.network_watcher_conn_mon_test_group_name if r.network_watcher_conn_mon_test_group_name else ''
        workspaceId = r.workspaceId if r.workspaceId else ''

        result.append(ResourceParameter(
            resourceId=resourceId,
            subscriptionId=subscriptionId,
            standardTestName=standardTestName,
            workspaceId=workspaceId,
            network_watcher_conn_mon_test_group_name=network_watcher_conn_mon_test_group_name
        ))
        
    return [True, result]

def get_resource_health_states(resources: List[ResourceParameter]) -> ResourceHealthResult:

    if not resources:
        return []
    
    healthStatuses = []
    
    for rsc in resources:

        client = HealthClient(appconfig)

        healthReport = client.get_health(rsc)

        healthStatuses.append(healthReport)

    return ResourceHealthResult(healthStatuses)



@app.get("/", status_code=200)
def root(response: fastapi.Response):
    response.headers["cwhd-version"] = appconfig.version
    return "alive"

@app.post("/RHRetriever", status_code=200)
def RHRetriever(req_body_param: RequestBodyParam, response: fastapi.Response):

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
        response.headers["cwhd-version"] = appconfig.version
        
        Log.debug('start main_request_RHRetriever')
        
        ok, resources = get_resource_params(req_body_param)

        if not ok:
            Log.exception('no resource ID supplied')
            response.status_code = 400
            return 'no resource ID supplied'

        rhState = get_resource_health_states(resources)

        return jsons.dumps(rhState)
        
    except Exception as e:
        Log.exception(f'error occured: {str(e)}')
        response.status_code = 500
        return str(e)
    

# powershell test
@app.post("/wara/runonce", status_code=202)
def run_pwsh():
    ap = WARAActionPlanner(config=appconfig)
    ap.run_wara()
    return 'accepted'


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)