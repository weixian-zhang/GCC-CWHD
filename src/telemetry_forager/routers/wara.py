import sys, os
from wara.wara_api import WARAApi
from fastapi import APIRouter
import log as Log
import fastapi
from init import appconfig
from wara.model import WARAExecution, WARARecommendation, WARAImpactedResource, WARAResourceType, WARARetirement
from memory_queue import MemoryQueue

# include parent dir to load module
sys.path.insert(1, os.path.join(sys.path[0], '..'))

router = APIRouter()

# init global queue
wara_report_gen_queue = MemoryQueue()

_waraapi = WARAApi(config=appconfig)


@router.get("/api/wara/report/runhistory", status_code=200, response_model=None)
def run_history(response: fastapi.Response) -> list[WARAExecution]:

    try:
        executions = _waraapi.list_execution_history()
        return executions
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@router.get("/api/wara/report/subscriptions", status_code=200, response_model=None)
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

@router.get("/api/wara/report/recommendations", status_code=200, response_model=None)
def get_recommendations(request: fastapi.Request, response: fastapi.Response)  -> list[WARARecommendation]:

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')
        implemented = params.get('implemented', 'All')
        impact = params.get('impact', 'All')
        resource_provider = params.get('rp', 'All')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        
        result = _waraapi.get_recommendations(subscription_id=subid, execution_id=executionid, implemented=implemented, 
                                              impact=impact, resource_provider=resource_provider, to_df=False)

        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@router.get("/api/wara/report/impactedresources", status_code=200, response_model=None)
def get_impacted_resources(request: fastapi.Request, response: fastapi.Response) -> list[WARAImpactedResource]:

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')
        impact = params.get('impact', 'All')
        resource_provider = params.get('rp', 'All')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_impacted_resources(subscription_id=subid, execution_id=executionid, 
                                                 impact=impact,resource_provider=resource_provider)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@router.get("/api/wara/report/impactedresourcetypes", status_code=200, response_model=None)
def get_impacted_resource_count(request: fastapi.Request, response: fastapi.Response) -> list[WARAResourceType]:

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')
        impact = params.get('impact', 'All')
        resource_provider = params.get('rp', 'All')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_impacted_resource_count(subscription_id=subid, execution_id= executionid, 
                                                      impact=impact, resource_provider=resource_provider)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

@router.get("/api/wara/report/retirements", status_code=200, response_model=None)
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


@router.get("/api/wara/report/resiliency-by-impact", status_code=200, response_model=None)
def get_resiliency_by_impact_stats(request: fastapi.Request, response: fastapi.Response):

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_resiliency_by_impact(subid, executionid)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)
    
@router.get("/api/wara/report/resource-by-impact", status_code=200, response_model=None)
def get_resources_by_impact(request: fastapi.Request, response: fastapi.Response):

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')
        resource_provider = params.get('rp', 'All')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_resources_by_impact(subid, executionid, resource_provider)
        return result
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)

    
@router.get("/api/wara/report/total-impact-count", status_code=200, response_model=None)
def get_total_impact_count(request: fastapi.Request, response: fastapi.Response):

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')
        impact = params.get('impact', 'All')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_total_impact_count(subid, executionid, impact=impact)
        return {'total_impact_count': result}
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)
    

@router.get("/api/wara/report/rp", status_code=200, response_model=None)
def get_resource_provider(request: fastapi.Request, response: fastapi.Response):
    '''
    returns unique list of resource providers
    '''

    try:

        params = request.query_params
        subid = params.get('subid', '')
        executionid = params.get('execid', '')

        if not subid or not executionid:
            response.status_code = 400
            return 'subscription_id and executionid are required'
        
        result = _waraapi.get_resource_provider(subid, executionid)
        return {'total_impact_count': result}
    
    except Exception as e:
        Log.exception(f'WARA/report - error occured: {str(e)}')
        response.status_code = 500
        return str(e)
    

@router.post("/api/wara/runonce", status_code=202)
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
