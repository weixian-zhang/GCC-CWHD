import sys
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))

import fastapi
from fastapi import APIRouter
import log as Log
from pydantic import BaseModel
from init import appconfig
from networkmap.manager import NetworkMapManager
from networkmap.model import NetworkMapResult
from datetime import datetime, timezone


class NetworkMapRequestBody(BaseModel):
    startTime: datetime
    endTime: datetime
    flowTypes: list[str] = []
    flowDirection: str = 'all'
    srcVNet: str = 'all'
    destVNet: str = 'all'
    srcSubnet: str = 'all'
    destSubnet: str = 'all'
    srcIP: str = 'all'
    destIP: str = 'all'

router = APIRouter()

nmap = NetworkMapManager(config=appconfig)

@router.post("/api/nmap/vnetflowlog", status_code=200, response_model=None)
def get_main_vnetfloqlog(body: NetworkMapRequestBody, response: fastapi.Response) -> NetworkMapResult:
    result = nmap.get_network_map_without_exyernalpublic_malicious(start_time=body.startTime,
                                  end_time=body.endTime,
                                  flow_types=body.flowTypes,
                                    flow_direction=body.flowDirection,
                                    src_vnet=body.srcVNet,
                                    dest_vnet=body.destVNet,
                                    src_subnet=body.srcSubnet,
                                    dest_subnet=body.destSubnet,
                                    src_ip=body.srcIP,
                                    dest_ip=body.destIP
                                  )
    return result