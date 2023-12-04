import pytest
import unittest.mock as mock
import sys
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcehealth import ResourceHealthMgmtClient
from pathlib import Path
parent_path = Path(__file__).parent.parent.resolve()._str
sys.path.insert(0, parent_path)


import function_app as func

@pytest.fixture
def func_api_params():
    return [
        {
            "subscriptionId": 'a',
            "resourceId": '/a/s/d/f/w'
        },
        {
            "subscriptionId": 'b',
            "resourceId": '/a/s/d/f/w'
        },
        {
            "subscriptionId": 'c',
            "resourceId": '/a/s/d/f/w'
        }
    ]


@pytest.fixture
def resource_health_api_result_available():
    global is_odd

    apir = mock.Mock()
    apir.location = 'southeastasia'
    apir.properties.availability_state = 'Available'
    apir.properties.summary = ''
    apir.properties.reported_time = datetime.now()
    apir.properties.occured_time = datetime.now()
    return apir

@pytest.fixture
def resource_health_api_result_Unavailable():
    global is_odd

    apir = mock.Mock()
    apir.location = 'southeastasia'
    apir.properties.availability_state = 'Unavailable'
    apir.properties.summary = ''
    apir.properties.reported_time = datetime.now()
    apir.properties.occured_time = datetime.now()
    return apir

# API health result
def test_ResourceHealthAPIResult_available():
    r = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    assert r.availabilityState == 1
    assert r.displayText == 'Available'

def test_ResourceHealthAPIResult_unavailable():
    r = func.ResourceHealthAPIResult('southeastasia,', 'Unavailable', '', datetime.now(), datetime.now() )
    assert r.availabilityState == 0
    assert r.displayText == 'Unavailable'

def test_ResourceHealthAPIResult_unknown():
    r = func.ResourceHealthAPIResult('southeastasia,', 'Unknown', '', datetime.now(), datetime.now() )
    assert r.availabilityState == 2
    assert r.displayText == 'Unknown'

# overall health
def test_overall_health_RHResult_all_available():
    r1 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    r2 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    r3 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    states = [r1, r2, r3]

    rh = func.RHResult(states)

    assert rh.overallHealth == 1

def test_overall_health_RHResult_1_unavailable():
    r1 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    r2 = func.ResourceHealthAPIResult('southeastasia,', 'Unavailable', '', datetime.now(), datetime.now() )
    r3 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    states = [r1, r2, r3]

    rh = func.RHResult(states)

    assert rh.overallHealth == 0

def test_overall_health_RHResult_1_Unknown():
    r1 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    r2 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    r3 = func.ResourceHealthAPIResult('southeastasia,', 'Unknown', '', datetime.now(), datetime.now() )
    states = [r1, r2, r3]

    rh = func.RHResult(states)

    assert rh.overallHealth == 0

def test_overall_health_RHResult_2_Unavailable():
    r1 = func.ResourceHealthAPIResult('southeastasia,', 'Unavailable', '', datetime.now(), datetime.now() )
    r2 = func.ResourceHealthAPIResult('southeastasia,', 'Available', '', datetime.now(), datetime.now() )
    r3 = func.ResourceHealthAPIResult('southeastasia,', 'Unavailable', '', datetime.now(), datetime.now() )
    states = [r1, r2, r3]

    rh = func.RHResult(states)

    assert rh.overallHealth == 0


# get resource health from mocked Resource Health API
def test_get_rh_states_from_api_empty_param(mock_ResourceHealthMgmtClient: mock.MagicMock, func_api_params):
    r = func.get_resource_health_states([])
    assert r == []

@mock.patch('function_app.create_rh_client')
def test_get_rh_states_from_api_with_available(create_rh_client, func_api_params, resource_health_api_result_available):
    
    apir = mock.Mock()
    apir.location = 'southeastasia'
    apir.properties.availability_state = 'Available'
    apir.properties.summary = ''
    apir.properties.reported_time = datetime.now()
    apir.properties.occured_time = datetime.now()
    
    rhClient = mock.Mock()
    asProp = mock.Mock()
    rhClient.availability_statuses = asProp
    asProp.get_by_resource = mock.MagicMock()
    asProp.get_by_resource.return_value = resource_health_api_result_available

    create_rh_client.return_value = rhClient
    
    rhStates = func.get_resource_health_states(func_api_params)

    assert len(rhStates.states) == 3
    assert rhStates.overallHealth == 1


@mock.patch('function_app.create_rh_client')
def test_get_rh_states_from_api_with_Unavailable(create_rh_client, func_api_params, resource_health_api_result_Unavailable):        
    
    rhClient = mock.Mock()
    asProp = mock.Mock()
    rhClient.availability_statuses = asProp
    asProp.get_by_resource = mock.Mock()
    asProp.get_by_resource.return_value = resource_health_api_result_Unavailable

    #asProp.get_by_resource.side_effect = side_effect_get_by_resource

    create_rh_client.return_value = rhClient
    
    rhStates = func.get_resource_health_states(func_api_params)

    assert len(rhStates.states) == 3
    assert rhStates.overallHealth == 0
    

    


