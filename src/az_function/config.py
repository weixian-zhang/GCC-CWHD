import json
import os

# standardTestName applies to App Service resource type only
class ResourceParameter:
    def __init__(self, resourceId, subscriptionId,standardTestName='' ) -> None:
        self.resourceId = resourceId
        self.subscriptionId = subscriptionId
        self.standardTestName = standardTestName

class HealthStatusThreshold:

    # diskUsagePercentage threshold is for all OS and data disk aggregated
    class VM:
        def __init__(self) -> None:
            self.cpuUsagePercentage = 70
            self.memoryUsagePercentage = 70
            self.diskUsagePercentage = 70

# example of threshold json 
# {
#     "metricUsageThreshold": {
#         "vm": {
#             "cpuUsagePercentage": 80,
#             "memoryUsagePercentage": 80,
#             "diskUsagePercentage": 80
#         }
#     }
# }
class AppConfig:
    def __init__(self) -> None:
        self.appinsightsInstrumentationKey = ''
        self.workspaceID: str = ''
        self.health_status_threshold = {}
        self.loaded: bool = False

    def load_from_envar(self):
        if self.loaded:
            return
        
        self.appinsightsInstrumentationKey = os.environ.get('AppinsightsInstrumentationKey')
        self.appinsightsConnString= os.environ.get('AppinsightsConnString')
        self.workspaceID = os.environ.get('WorkspaceID')

        thresholds = json.loads(os.environ.get('HealthStatusThreshold'))

        self.health_status_threshold = self.get_thresholds(thresholds)

        if not self.workspaceID: # or not mapJson:
            raise Exception('necessary environment variables not found')

        self.loaded = True

    def get_thresholds(self, thresholds: dict) -> HealthStatusThreshold:
        th = thresholds['metricUsageThreshold']

        ht = HealthStatusThreshold()
        ht.VM = HealthStatusThreshold.VM()
        
        ht.VM.cpuUsagePercentage =  th['vm']['cpuUsagePercentage']
        ht.VM.memoryUsagePercentage =  th['vm']['memoryUsagePercentage']
        ht.VM.diskUsagePercentage =  th['vm']['diskUsagePercentage']

        return ht
        
