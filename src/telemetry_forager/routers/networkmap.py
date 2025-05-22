import sys
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))

import fastapi
from fastapi import APIRouter
import log as Log
from pydantic import BaseModel
from init import appconfig
from networkmap.manager import NetworkMapManager
from networkmap.model import NetworkMapResult, FilterDataResult
from datetime import datetime


class NetworkMapRequestBody(BaseModel):
    startTime: datetime
    endTime: datetime
    flowTypes: list[str] = []
    flowDirection: str = 'all'
    srcSubscription: list[str] = []
    srcRG: list[str] = []
    destSubscription: list[str] = []
    destRG: list[str] = []
    srcVNet: list[str] = []
    destVNet: list[str] = []
    srcSubnet: list[str] = []
    destSubnet: list[str] = []
    srcIP: list[str] = []
    destIP: list[str] = []
    duration: list[float] = []
    src_payload_size: list[str] = []
    dest_payload_size: list[str] = []
    rowLimit: int = 5000

class FilterDataRequestBody(BaseModel):
  startTime: datetime
  endTime: datetime
  flowTypes: list[str] = []
  flowDirection: str = 'all'
  rowLimit: int = 5000


router = APIRouter()

nmap = NetworkMapManager(config=appconfig)

min_row_limit = 1
max_row_limit = 15000

@router.post("/api/nmap/vnetflowlog", status_code=200, response_model=None)
def get_main_vnetflowlog(body: NetworkMapRequestBody, response: fastapi.Response) -> NetworkMapResult:

    if not min_row_limit <= body.rowLimit <= max_row_limit:
        body.rowLimit = max_row_limit

    result = nmap.get_network_map(
                                  start_time=body.startTime,
                                  end_time=body.endTime,
                                  flow_types=body.flowTypes,
                                  flow_direction=body.flowDirection,
                                  src_subscrition=body.srcSubscription,
                                  dest_subscription=body.destSubscription,
                                  src_rg=body.srcRG,
                                  dest_rg=body.destRG,
                                  src_vnet=body.srcVNet,
                                  dest_vnet=body.destVNet,
                                  src_subnet=body.srcSubnet,
                                  dest_subnet=body.destSubnet,
                                  src_ip=body.srcIP,
                                  dest_ip=body.destIP,
                                  duration=body.duration,
                                  src_payload_size=body.src_payload_size,
                                  dest_payload_size=body.dest_payload_size,
                                  row_limit=body.rowLimit,
                                  )
    return result

@router.post("/api/nmap/filterdata", status_code=200, response_model=None)
def get_filter_data(body: FilterDataRequestBody, response: fastapi.Response) -> FilterDataResult:

    if not min_row_limit <= body.rowLimit <= max_row_limit:
        body.rowLimit = max_row_limit
        
    result = nmap.get_filter_data(start_time=body.startTime,
                                  end_time=body.endTime,
                                  flow_types=body.flowTypes,
                                  flow_direction=body.flowDirection,
                                  row_limit=body.rowLimit)
    return result


# @router.post("/api/nmap/src/subscription", status_code=200, response_model=None)
# def get_src_subscription(body: FilterDataRequestBody, response: fastapi.Response) -> dict:
    
#     result = nmap.get_unique_src_subscription(current_data_key=body.current_data_key)
#     return result


# @router.post("/api/nmap/src/rg", status_code=200, response_model=None)
# def get_src_rg(body: FilterDataRequestBody, response: fastapi.Response) -> dict:


#     result = nmap.get_unique_src_rg(current_data_key=body.current_data_key)
#     return result

# @router.post("/api/nmap/src/vnet", status_code=200, response_model=None)
# def get_src_vnet(body: FilterDataRequestBody, response: fastapi.Response) -> dict:


#     result = nmap.get_unique_src_vnet(current_data_key=body.current_data_key)
#     return result



# @router.post("/api/nmap/src/subnet", status_code=200, response_model=None)
# def get_src_subnet(body: FilterDataRequestBody, response: fastapi.Response) -> dict:

#     result = nmap.get_unique_src_subnet(current_data_key=body.current_data_key)
#     return result


# @router.post("/api/nmap/src/ip", status_code=200, response_model=None)
# # def get_main_vnetflowlog(body: FilterDataRequestBody, response: fastapi.Response) -> dict:
# def get_src_ip(body: FilterDataRequestBody, response: fastapi.Response) -> dict:

#     result = nmap.get_unique_src_ip(current_data_key=body.current_data_key)
#     return result


# @router.post("/api/nmap/dest/subscription", status_code=200, response_model=None)
# def get_dest_subscription(body: FilterDataRequestBody, response: fastapi.Response) -> dict:


#     result = nmap.get_unique_dest_subscription(current_data_key=body.current_data_key)
#     return result

# @router.post("/api/nmap/dest/rg", status_code=200, response_model=None)
# def get_dest_rg(body: FilterDataRequestBody, response: fastapi.Response) -> dict:

#     result = nmap.get_unique_dest_rg(current_data_key=body.current_data_key)
#     return result

# @router.post("/api/nmap/dest/vnet", status_code=200, response_model=None)
# def get_dest_vnet(body: FilterDataRequestBody, response: fastapi.Response) -> dict:

#     result = nmap.get_unique_dest_vnet(current_data_key=body.current_data_key)
#     return result

# @router.post("/api/nmap/dest/subnet", status_code=200, response_model=None)
# def get_dest_subnet(body: FilterDataRequestBody, response: fastapi.Response) -> dict:

#     result = nmap.get_unique_dest_subnet(current_data_key=body.current_data_key)
#     return result

# @router.post("/api/nmap/dest/ip", status_code=200, response_model=None)
# def get_dest_ip(body: FilterDataRequestBody, response: fastapi.Response) -> dict:

#     result = nmap.get_unique_dest_ip(current_data_key=body.current_data_key)

#     return result