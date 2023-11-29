import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcehealth import ResourceHealthMgmtClient
import os
import logging
from datetime import datetime
import jsons

#override Azure's root logger to be able to log to console
logger = logging.getLogger('akshay')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

class ResourceHealthAPIResult:

    # availabilityState
    # Available = 1, Unavailable = 0 or Unknown = 2
    # converting into number is easier to style by Grafana "threshold" 

    def __init__(self, location='', availabilityState=2, summary='', reportedTime=None, stateLastChangeTime=None) -> None:

        if availabilityState == 'Available':
            availabilityState = 1
        elif availabilityState == 'Unavailable':
            availabilityState = 0
        else:
            availabilityState = 2

        self.location = location
        self.availabilityState = availabilityState
        self.summary = summary
        self.reportedTime = (reportedTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
        self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
        self.summaryForDisplay = f'''
        {self.summary}
        reported at: {self.reportedTime}
        '''


class RHResult:
    def __init__(self, states: list[ResourceHealthAPIResult]) -> None:

        # overallHealth
        # Available = 1, Unavailable = 0, Partial = 2
        # converting into number is easier to style by Grafana "threshold"

        self.overallHealth = 1
        self.overallSummary = ''

        self.states: list[ResourceHealthAPIResult] = states

        self.set_overall_state()

    def set_overall_state(self):

        if not self.states:
            return
        
        if all([x.availabilityState == 1 for x in self.states]):
            self.overallHealth = 1
            self.overallSummary = 'All dependent services are available'
        elif all([x.availabilityState == 0 for x in self.states]):
            self.overallHealth = 0
            self.overallSummary = 'All dependent services are unavailable'
        else:
            self.overallHealth = 2
            self.overallSummary = 'Partial dependent services are available'

def get_resource_ids(reqBody) -> list[str]:
    if not reqBody:
        return []
    
    return reqBody['resources']

def get_resource_health_states(resources: list[str]) -> RHResult:

    if not resources:
        return []
    
    states = []
    
    for rsc in resources:

        subId = rsc['subscriptionId']
        rscId = rsc['resourceId']

        logger.debug(f'retrieving availability status for resource {rscId}')

        client = ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id=subId)

        asResult = client.availability_statuses.get_by_resource(resource_uri=rscId)

        logger.debug(f'availability status retrieved successfully for resource {rscId}')

        apir = ResourceHealthAPIResult(location=asResult.location,
                                       availabilityState=asResult.properties.availability_state,
                                       summary=asResult.properties.summary,
                                       reportedTime=asResult.properties.reported_time,
                                       stateLastChangeTime=asResult.properties.occured_time)
        
        states.append(apir)

    return RHResult(states)
    


app = func.FunctionApp()

@app.route(route="RHRetriever", auth_level=func.AuthLevel.FUNCTION)
def HRRetriever(req: func.HttpRequest) -> func.HttpResponse:

    '''
    requires 4 environment variables:
        AZURE_SUBSCRIPTION_ID,
        AZURE_CLIENT_ID,
        AZURE_CLIENT_SECRET,
        AZURE_TENANT_ID,
    '''
    
    try:
        logger.debug('request received')

        req_body = req.get_json()

        resourceIds = get_resource_ids(req_body)

        if not resourceIds:
            logger.debug('no resource ID supplied')
            return func.HttpResponse('no resource ID supplied', status_code=400)

        rhState = get_resource_health_states(resourceIds)
        
        logger.debug('request completed, returning result')

        return func.HttpResponse(
                                jsons.dumps(rhState),
                                status_code=200)

    except Exception as e:
        logger.debug(f'error occured: {str(e)}')
        return func.HttpResponse(str(e), status_code=500)
