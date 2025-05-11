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
    srcSubscription: str = 'all'
    srcRG: str = 'all'
    destSubscription: str = 'all'
    destRG: str = 'all'
    srcVNet: str = 'all'
    destVNet: str = 'all'
    srcSubnet: str = 'all'
    destSubnet: str = 'all'
    srcIP: str = 'all'
    destIP: str = 'all'

class FilterDataRequestBody(BaseModel):
  startTime: datetime
  endTime: datetime
  flowTypes: list[str] = []

router = APIRouter()

nmap = NetworkMapManager(config=appconfig)

@router.post("/api/nmap/vnetflowlog", status_code=200, response_model=None)
def get_main_vnetflowlog(body: NetworkMapRequestBody, response: fastapi.Response) -> NetworkMapResult:
    result = nmap.get_network_map_without_externalpublic_malicious(
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
                                  dest_ip=body.destIP
                                  )
    return result


@router.post("/api/nmap/src/subscription", status_code=200, response_model=None)
def get_src_subscription(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    # result = nmap.get_unique_src_subscription(flow_types=body.flowTypes,
    #                               start_time=body.startTime,
    #                               end_time=body.endTime)
    result = nmap.get_unique_src_subscription(
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
                                  dest_ip=body.destIP)
    return result


@router.post("/api/nmap/src/rg", status_code=200, response_model=None)
def get_main_vnetflowlog(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_src_rg(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result

@router.post("/api/nmap/src/vnet", status_code=200, response_model=None)
def get_main_vnetflowlog(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_src_vnet(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result



@router.post("/api/nmap/src/subnet", status_code=200, response_model=None)
def get_main_vnetflowlog(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_src_subnet(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result


@router.post("/api/nmap/src/ip", status_code=200, response_model=None)
def get_main_vnetflowlog(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_src_ip(
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
                                  dest_ip=body.destIP
                                  )
    return result


@router.post("/api/nmap/dest/subscription", status_code=200, response_model=None)
def get_dest_subscription(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_dest_subscription(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result

@router.post("/api/nmap/dest/rg", status_code=200, response_model=None)
def get_dest_rg(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_dest_rg(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result

@router.post("/api/nmap/dest/vnet", status_code=200, response_model=None)
def get_dest_vnet(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_dest_vnet(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result

@router.post("/api/nmap/dest/subnet", status_code=200, response_model=None)
def get_dest_subnet(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_dest_subnet(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result

@router.post("/api/nmap/dest/ip", status_code=200, response_model=None)
def get_dest_ip(body: NetworkMapRequestBody, response: fastapi.Response) -> dict:
    result = nmap.get_unique_dest_ip(start_time=body.startTime,
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
                                  dest_ip=body.destIP)
    return result