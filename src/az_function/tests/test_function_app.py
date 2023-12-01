import pytest
import unittest.mock as mock
import sys
from datetime import datetime
from pathlib import Path
parent_path = Path(__file__).parent.parent.resolve()._str
sys.path.insert(0, parent_path)

import function_app as func

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




if __name__ == '__main__':
    pass