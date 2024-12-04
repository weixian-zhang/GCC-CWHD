import json
import os
from model import HealthStatusThreshold, ResourceParameter


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
        self.health_status_threshold = {}
        self.loaded: bool = False

    def load_from_envar(self):
        if self.loaded:
            return
        
        self.queryTimeSpanHour = os.environ.get('QueryTimeSpanHour') if os.environ.get('QueryTimeSpanHour') else 2
        self.appinsightsConnString= os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

        thresholds = json.loads(os.environ.get('HealthStatusThreshold'))

        self.health_status_threshold = self.get_thresholds(thresholds)

        if not self.health_status_threshold or not self.appinsightsConnString:
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
        
