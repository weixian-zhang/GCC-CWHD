import sys, os
from typing import List
from health import HealthClient
import fastapi
from fastapi import APIRouter
import log as Log
from model import ResourceParameter, ResourceHealthResult
from pydantic import BaseModel
from init import appconfig


# # load environment variables
# appconfig = AppConfig()
# # load env vars
# appconfig.load_from_envar()

# include parent dir to load module
sys.path.insert(1, os.path.join(sys.path[0], '..'))

router = APIRouter()

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


@router.get("/", status_code=200)
def root(response: fastapi.Response):
    raise Exception("This endpoint is not available. Please use /health instead.")
    response.headers["cwhd-version"] = appconfig.version
    return "alive"

# health status
@router.post("/RHRetriever", status_code=200)
def RHRetriever(req_body_param: RequestBodyParam, response: fastapi.Response):

    """
    returns overall health status that powers colored tiles on Grafana
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

        return rhState
        
    except Exception as e:
        Log.exception(f'Health/resource - error occured: {str(e)}')
        response.status_code = 500
        return str(e)