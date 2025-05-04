# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).absolute().parent))


from config import AppConfig
from azure.monitor.query import LogsQueryClient
from azure.monitor.query._models import LogsQueryStatus
from azure.identity import DefaultAzureCredential
import datetime
from datetime import datetime, timedelta, timezone
import pandas as pd
import log as Log
from azure.core.exceptions import HttpResponseError
from network_map_kql import NetworkmapKQL
from networkmap.networkmap_model import NetworkMapModel, NetworkMapVnetFlowLog, NetworkMapVnetFlowLogResult

class NetworkMapManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.law_client = LogsQueryClient(DefaultAzureCredential())

    def get_main_vnet_flow_log(self, start_time: datetime, end_time: datetime) -> dict:
        
        # start_time=datetime(2025, 4, 30, tzinfo=timezone.utc)
        # end_time=datetime(2025, 5, 4, tzinfo=timezone.utc)

        try:

            result = {}

            response =  self.law_client.query_workspace(
                        workspace_id= self.config.networkmap_workspace_id,
                        query=vnet_flow_log,
                        timespan=(start_time, end_time)
                    )

            if response.status == LogsQueryStatus.SUCCESS:
                table = response.tables[0]
                df = pd.DataFrame(data=table.rows, columns=table.columns)
                result = df.to_dict(orient='records')

            return result

        except HttpResponseError as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}
        except Exception as e:
            Log.exception(f'NetworkMapManager - error occured: {str(e)}')
            return {}
