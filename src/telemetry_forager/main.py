import json
from typing import List
import fastapi #import FastAPI, Response
import uvicorn
from pydantic import BaseModel
from health import HealthClient
import jsons
from config import AppConfig
from model import ResourceParameter, ResourceHealthResult
import log as Log
from job import WARAEventLoop, WARAApiGenScheduledJob, WARAHistoryCleanUpScheduledJob
from telemetry_forager.wara.wara_api import WARAApi
from wara.model import WARAExecution, WARARecommendation, WARAImpactedResource, WARAResourceType, WARARetirement
from memory_queue import MemoryQueue


# init global queue
wara_report_gen_queue = MemoryQueue()

# load environment variables
appconfig = AppConfig()
# load env vars
appconfig.load_from_envar()

Log.init(appconfig)

app = fastapi.FastAPI()

_waraapi = WARAApi(config=appconfig)

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
        Log.exception(f'Health/resource - error occured: {str(e)}')
        response.status_code = 500
        return str(e)
    
    
# WARA module

@app.get("/api/wara/report/runhistory", status_code=200, response_model=None)
def run_history(response: fastapi.Response) -> list[WARAExecution]:

    try:
        executions = _waraapi.list_execution_history()
        return executions
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@app.get("/api/wara/report/subscriptions", status_code=200, response_model=None)
def get_subscriptions(request: fastapi.Request, response: fastapi.Response)  -> list[WARARecommendation]:

    try:

        params = request.query_params
        executionid = params.get('execid', '')

        if not executionid:
            response.status_code = 400
            return 'executionid are required'
        
        result = _waraapi.get_run_subscriptions(executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@app.get("/api/wara/report/recommendations", status_code=200, response_model=None)
def get_recommendations(request: fastapi.Request, response: fastapi.Response)  -> list[WARARecommendation]:

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        
        result = _waraapi.get_recommendations(subid, executionid)

        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@app.get("/api/wara/report/impactedresources", status_code=200, response_model=None)
def get_impacted_resources(request: fastapi.Request, response: fastapi.Response) -> list[WARAImpactedResource]:

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_impacted_resources(subid, executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@app.get("/api/wara/report/impactedresourcetypes", status_code=200, response_model=None)
def get_resource_types(request: fastapi.Request, response: fastapi.Response) -> list[WARAResourceType]:

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_impacted_resource_types(subid, executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)


@app.get("/api/wara/report/retirements", status_code=200, response_model=None)
def get_retirements(request: fastapi.Request, response: fastapi.Response) -> list[WARARetirement]:

    try:
        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_retirements(subid, executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)


@app.get("/api/wara/report/stats/service-by-impact", status_code=200, response_model=None)
def get_recommendation_service_type_by_impact_stats(request: fastapi.Request, response: fastapi.Response):

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_pivot_recommendation_service_by_impact(subid, executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)


@app.get("/api/wara/report/stats/resiliency-by-impact", status_code=200, response_model=None)
def get_resiliency_by_impact_stats(request: fastapi.Request, response: fastapi.Response):

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_pivot_recommendation_resiliency_by_impact(subid, executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)
    

@app.post("/api/wara/runonce", status_code=202)
def run_pwsh(response: fastapi.Response):
    '''
    current logic is to accept only 1 task in the queue to prevent spamming
    '''
    
    try:

        wara_report_gen_queue.enqueue('run_wara')
        return json.dumps({'status': 'success', 'queue_len': f'{len(wara_report_gen_queue)}'})
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)


# run background jobs
WARAEventLoop().start()
WARAApiGenScheduledJob().init_wara_report_gen_scheduled_job()
WARAHistoryCleanUpScheduledJob().init_clean_history_scheduled_job()

# execute wara 1 time upon startup
wara_report_gen_queue.enqueue('run_wara')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)