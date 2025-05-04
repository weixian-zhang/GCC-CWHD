# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).absolute().parent))

import fastapi
from fastapi import APIRouter
import log as Log
from pydantic import BaseModel
from init import appconfig
from networkmap.networkmap_manager import NetworkMapManager
from datetime import datetime, timezone


class NetworkMapRequestBody(BaseModel):
    startTime: datetime
    endTime: datetime
    flow_types: list[str] = []
    src_vnet: str = ''
    dest_vnet: str = ''
    src_subnet: str = ''
    dest_subnet: str = ''
    src_ip: str = ''
    dest_ip: str = ''

router = APIRouter()

nmap = NetworkMapManager(config=appconfig)

@router.post("/api/nmap/vnetflowlog", status_code=200)
def get_main_vnetfloqlog(reqbody: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    pass