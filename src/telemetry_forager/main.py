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
from wara.wara_executor import WARAExecutor
from wara.wara_report import WARAReport
from wara.model import WARAExecution, WARARecommendation, WARAImpactedResource, WARAResourceType, WARARetirement
from opentelemetry.propagate import extract
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from memory_queue import MemoryQueue


# init global queue
mem_queue = MemoryQueue()

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
    
# WARA module

@app.get("/api/wara/report/runhistory", status_code=200, response_model=None)
def run_history() -> list[WARAExecution]:
    wr = WARAReport(config=appconfig)
    executions = wr.list_execution_history()
    return executions

@app.get("/api/wara/report/subscriptions", status_code=200, response_model=None)
def get_subscriptions(request: fastapi.Request, response: fastapi.Response)  -> list[WARARecommendation]:
    params = request.query_params
    executionid = params.get('execid', '')

    if not executionid:
        response.status_code = 400
        return 'executionid are required'
    
    wr = WARAReport(config=appconfig)
    result = wr.get_run_subscriptions(executionid)
    return result

@app.get("/api/wara/report/recommendations", status_code=200, response_model=None)
def get_recommendations(request: fastapi.Request, response: fastapi.Response)  -> list[WARARecommendation]:
    params = request.query_params
    subid = params.get('subid', '')
    executionid = params.get('execid', '')

    if not subid or not executionid:
        response.status_code = 400
        return 'subscription_id and executionid are required'
    
    wr = WARAReport(config=appconfig)
    
    result = wr.get_recommendations(subid, executionid)

    return result

@app.get("/api/wara/report/impactedresources", status_code=200, response_model=None)
def get_impacted_resources(request: fastapi.Request, response: fastapi.Response) -> list[WARAImpactedResource]:
    params = request.query_params
    subid = params.get('subid', '')
    executionid = params.get('execid', '')

    if not subid or not executionid:
        response.status_code = 400
        return 'subscription_id and executionid are required'
    
    wr = WARAReport(config=appconfig)
    result = wr.get_impacted_resources(subid, executionid)
    return result

@app.get("/api/wara/report/impactedresourcetypes", status_code=200, response_model=None)
def get_resource_types(request: fastapi.Request, response: fastapi.Response) -> list[WARAResourceType]:
    params = request.query_params
    subid = params.get('subid', '')
    executionid = params.get('execid', '')

    if not subid or not executionid:
        response.status_code = 400
        return 'subscription_id and executionid are required'
    
    wr = WARAReport(config=appconfig)
    result = wr.get_impacted_resource_types(subid, executionid)
    return result


@app.get("/api/wara/report/retirements", status_code=200, response_model=None)
def get_retirements(request: fastapi.Request, response: fastapi.Response) -> list[WARARetirement]:
    params = request.query_params
    subid = params.get('subid', '')
    executionid = params.get('execid', '')

    if not subid or not executionid:
        response.status_code = 400
        return 'subscription_id and executionid are required'
    
    wr = WARAReport(config=appconfig)
    result = wr.get_retirements(subid, executionid)
    return result


@app.get("/api/wara/report/stats/service-by-impact", status_code=200, response_model=None)
def get_recommendation_service_type_by_impact_stats(request: fastapi.Request, response: fastapi.Response):
    params = request.query_params
    subid = params.get('subid', '')
    executionid = params.get('execid', '')

    if not subid or not executionid:
        response.status_code = 400
        return 'subscription_id and executionid are required'
    
    wr = WARAReport(config=appconfig)
    result = wr.get_pivot_recommendation_service_by_impact(subid, executionid)
    return result


@app.get("/api/wara/report/stats/resiliency-by-impact", status_code=200, response_model=None)
def get_resiliency_by_impact_stats(request: fastapi.Request, response: fastapi.Response):
    params = request.query_params
    subid = params.get('subid', '')
    executionid = params.get('execid', '')

    if not subid or not executionid:
        response.status_code = 400
        return 'subscription_id and executionid are required'
    
    wr = WARAReport(config=appconfig)
    result = wr.get_pivot_recommendation_resiliency_by_impact(subid, executionid)
    return result
    

@app.post("/api/wara/runonce", status_code=202)
def run_pwsh():
    mem_queue.enqueue('run_wara')
    return json.dumps({'status': 'success'})


# background task
def always_running_job_generate_wara_report():
    while True:
        try:
            task = mem_queue.dequeue()
            if task:
                Log.debug('always_running_job receive task wara-report-generation')
                wap = WARAExecutor(config=appconfig)
                wap.run()
            time.sleep(5)
        except Exception as e:
            Log.exception(f'error occured at always_running_job_generate_wara_report: {str(e)}')
        

def scheduled_job_generate_wara_report():
     Log.debug('scheduled_job enqueue task wara-report-generation')
     mem_queue.enqueue('run_wara')

# cron schedule default to 3 hours
def setup_scheduled_job():
    scheduler = BackgroundScheduler()
    scheduler.start()
    trigger = CronTrigger(
        year="*", month="*", day="*", hour="*/3", minute="0", second="0"
    )
    scheduler.add_job(
        scheduled_job_generate_wara_report,
        trigger=trigger,
        name="Background_Task_WARA_Report_Generation",
    )

    Log.debug('scheduled_job is setup successfully')

# setup background tasks
# Create and start a new thread
thread = threading.Thread(target=always_running_job_generate_wara_report)
thread.start()

setup_scheduled_job()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)