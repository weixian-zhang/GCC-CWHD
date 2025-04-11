import logging
from config import AppConfig
from opencensus.ext.azure.log_exporter import AzureLogHandler
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import (
    SpanKind,
    get_tracer_provider,
    set_tracer_provider,
)
from opentelemetry.propagate import extract
import os

# Get a tracer for the current module.
tracer = trace.get_tracer(__name__,
                          tracer_provider=get_tracer_provider())

#override Azure's root logger to be able to log to console
# logger = logging.getLogger('akshay')
# logger.setLevel(logging.ERROR)

logging.basicConfig(level = logging.WARNING)
logger = logging.getLogger('azure')
sh = logging.StreamHandler()
sh.setLevel(logging.WARNING)
logger.propagate = False
logger.addHandler(sh)

loaded = False

def init(appconfig: AppConfig) -> None:
        global loaded
        
        if not appconfig:
            raise('Error initializing logger as appconfig is None')
        
        if not loaded:
             loaded = True
        else:
             return
        

        appinsightsExceptionHandler = AzureLogHandler(connection_string=appconfig.appinsightsConnString)
        appinsightsExceptionHandler.setLevel(logging.ERROR)
        logger.addHandler(appinsightsExceptionHandler)

        appinsightsWarnHandler = AzureLogHandler(connection_string=appconfig.appinsightsConnString)
        appinsightsWarnHandler.setLevel(logging.WARNING)
        logger.addHandler(appinsightsWarnHandler)
        

def debug(msg):
    logger.debug(msg)


def exception(msg):
    logger.exception(msg)

def exception(msg, **kwargs):

    appinsightsCusomtProps = {'custom_dimensions': {}}
    for k, v in kwargs.items():
        appinsightsCusomtProps['custom_dimensions'][k] = v

    logger.exception(msg,stack_info=True, exc_info=True, extra=appinsightsCusomtProps)

def warn(msg, **kwargs):

    if not kwargs:
         logger.warning(msg, exc_info=True, stack_info=True)
         return

    appinsightsCusomtProps = {'custom_dimensions': {}}
    for k, v in kwargs.items():
        appinsightsCusomtProps['custom_dimensions'][k] = v

    logger.warning(msg, extra=appinsightsCusomtProps)


def get_tracer():
     return tracer
