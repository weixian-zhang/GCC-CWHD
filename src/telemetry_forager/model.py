

# standardTestName applies to App Service resource type only
class ResourceParameter:
    def __init__(self, resourceId, subscriptionId, workspaceId='', standardTestName='', network_watcher_conn_mon_test_group_name='') -> None:
        self.resourceId = resourceId
        self.subscriptionId = subscriptionId
        self.workspaceId = workspaceId
        self.standardTestName = standardTestName
        self.network_watcher_conn_mon_test_group_name = network_watcher_conn_mon_test_group_name

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
                 availabilityState=0, 
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
    

# class ResourceHealthAPIResult:

#     # availabilityState
#     # Available = 1, Unavailable = 0 or Unknown = 2
#     # converting into number is easier to style by Grafana "threshold" 

#     def __init__(self, 
#                  location='', 
#                  availabilityState='', 
#                  summary='', 
#                  reportedTime=None, 
#                  stateLastChangeTime=None) -> None:

#         self.location = location
#         self.availabilityState = availabilityState
#         self.summary = summary
#         self.reportedTime = (reportedTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
#         self.stateLastChangeTime = (stateLastChangeTime if not None else datetime.now()).strftime("%B %d, %Y %H:%M:%S")
#         self.displayText = ''

#         if availabilityState == 'Available':
#             self.availabilityState = 1
#             self.displayText = 'Available'
#         elif availabilityState == 'Unavailable':
#             self.availabilityState = 0
#             self.displayText = 'Unavailable'
#         else:
#             self.availabilityState = 2
#             self.displayText = 'Unknown'

class ResourceHealthResult:
    def __init__(self, states: list[HealthReport]) -> None: #list[ResourceHealthAPIResult]) -> None:

        # overallHealth
        # Available = 1, Unavailable = 0, Partial = 2
        # converting into number is easier to style by Grafana "threshold"

        self.overallHealth = 1
        self.overallSummary = ''

        self.states: list[HealthReport] = states

        self.set_overall_health_state()

    def set_overall_health_state(self):

        if not self.states:
            return
        
        if all([x.availabilityState == 1 for x in self.states]):
            self.overallHealth = 1
            self.overallSummary = 'Available'
            return
        
        if any([x.availabilityState == 0 for x in self.states]):
            self.overallHealth = 0
            self.overallSummary = 'Unavailable'
            return
        
        if any([x.availabilityState == 2 for x in self.states]):
            self.overallHealth = 2
            self.overallSummary = 'Warning'