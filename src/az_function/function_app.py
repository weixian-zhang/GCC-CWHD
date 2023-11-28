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

    def __init__(self, location='', availabilityState=2, summary='', occuredTime=None) -> None:

        if availabilityState == 'Available':
            availabilityState = 1
        elif availabilityState == 'Unavailable':
            availabilityState = 0
        else:
            availabilityState = 2

        self.location = location
        self.availabilityState = availabilityState
        self.summary = summary
        self.occuredTime = occuredTime if not None else datetime.now()


class RHResult:
    def __init__(self, states: list[ResourceHealthAPIResult]) -> None:

        # overallHealth
        # Available = 1, Unavailable = 0, Partial = 2
        # converting into number is easier to style by Grafana "threshold"

        self.overallHealth = 1
        self.states: list[ResourceHealthAPIResult] = states

        self.set_overall_state()

    def set_overall_state(self):

        if not self.states:
            return
        
        if all([x.availabilityState == 1 for x in self.states]):
            self.overallHealth = 1
        elif all([x.availabilityState == 0 for x in self.states]):
            self.overallHealth = 0
        else:
            self.overallHealth = 2

def get_resource_ids(reqBody) -> list[str]:
    if not reqBody:
        return []
    
    return reqBody['resourceIds']

def get_resource_health_states(rscIds: list[str]) -> RHResult:

    if not rscIds:
        return []
    
    states = []
    
    sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")

    client = ResourceHealthMgmtClient(credential=DefaultAzureCredential(), subscription_id=sub_id)

    for rscID in rscIds:

        logger.debug(f'retrieving availability status for resource {rscID}')

        asResult = client.availability_statuses.get_by_resource(resource_uri=rscID)

        logger.debug(f'availability status retrieved successfully for resource {rscID}')

        apir = ResourceHealthAPIResult(location=asResult.location,
                                       availabilityState=asResult.properties.availability_state,
                                       summary=asResult.properties.summary,
                                       occuredTime=asResult.properties.occured_time)
        
        states.append(apir)

    return RHResult(states)
    


app = func.FunctionApp()

@app.route(route="HRRetriever", auth_level=func.AuthLevel.FUNCTION)
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
