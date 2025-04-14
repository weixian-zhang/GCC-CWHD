import json
import os
import sys
from model import HealthStatusThreshold, ResourceParameter
from dotenv import load_dotenv


load_dotenv()
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

    def debugger_is_active(self) -> bool:
        """Return if the debugger is currently active"""
        return hasattr(sys, 'gettrace') and sys.gettrace() is not None

    def load_from_envar(self):
        if self.loaded:
            return
        
        self.version = os.environ.get('Version') if os.environ.get('Version') else '1.1'
        self.queryTimeSpanHour = int(os.environ.get('QueryTimeSpanHour')) if os.environ.get('QueryTimeSpanHour') else 2
        self.appinsightsConnString= os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING') if os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING') else ''
        self.health_status_threshold = self.get_thresholds()

        self.wara_tenantId = os.environ.get('WARA_TenantId') if os.environ.get('WARA_TenantId') else ''

        self.table_storage_url = os.environ.get('Table_Storage_URL') if os.environ.get('Table_Storage_URL') else ''

        self.wara_days_to_keep_run_history= int(os.environ.get('WARA_Days_To_Keep_Run_History')) if os.environ.get('WARA_Days_To_Keep_Run_History') else 180

        self.timezone = os.environ.get('Timezone') if os.environ.get('Timezone') else 'Asia/Singapore'

        enable_wara = os.environ.get('Enable_WARA')
        self.enable_wara = True if enable_wara and enable_wara.lower() == 'true' else False
        
        self.loaded = True

    def get_thresholds(self) -> HealthStatusThreshold:

        try:
            thresholds = os.environ.get('HealthStatusThreshold') #json.loads(os.environ.get('HealthStatusThreshold'))

            if not thresholds:
                thresholds = json.loads('{     "metricUsageThreshold": {         "vm": {             "cpuUsagePercentage": 80,             "memoryUsagePercentage": 80,             "diskUsagePercentage": 80         }     } }')
            else:
                thresholds = json.loads(thresholds)

            th = thresholds['metricUsageThreshold']

            ht = HealthStatusThreshold()
            ht.VM = HealthStatusThreshold.VM()
            
            ht.VM.cpuUsagePercentage =  th['vm']['cpuUsagePercentage']
            ht.VM.memoryUsagePercentage =  th['vm']['memoryUsagePercentage']
            ht.VM.diskUsagePercentage =  th['vm']['diskUsagePercentage']

            return ht
        except Exception as e:
            raise Exception(f'Error in parsing config HealthStatusThreshold {e}')
        
        

    
        
        
        
