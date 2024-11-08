

# standardTestName applies to App Service resource type only
class ResourceParameter:
    def __init__(self, resourceId, subscriptionId,standardTestName='', workspaceId='') -> None:
        self.resourceId = resourceId
        self.subscriptionId = subscriptionId
        self.standardTestName = standardTestName
        self.workspaceId = workspaceId

class HealthStatusThreshold:

    # diskUsagePercentage threshold is for all OS and data disk aggregated
    class VM:
        def __init__(self) -> None:
            self.cpuUsagePercentage = 70
            self.memoryUsagePercentage = 70
            self.diskUsagePercentage = 70


class HealthReport:
    """
    A general data model used a a consistent return type for all health status result
    """
    # availabilityState
    # Available = 1, Unavailable = 0 or Unknown = 2
    # converting into number is easier to style by Grafana "threshold" 

    def __init__(self,
                 resourceId='',
                 description='', 
                 availabilityState='', 
                 summary='', 
                 reportedTime=None, 
                 stateLastChangeTime=None) -> None:
        
        self.availabilityState = availabilityState
        self.resourceId = resourceId
        self.description = description
        self.reportedTime = (reportedTime if not None else datetime.now())

        #self.location = location    # obsolete, to be deleted
        self.summary = summary      # obsolete, to be deleted
        self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now())    # obsolete, to be deleted
        self.displayText = '' # obsolete, to be deleted

    @staticmethod
    def query_no_result_msg():
        return f'health status log or metric result not found'