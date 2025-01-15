import logging
from loguru import logger
from config import AppConfig
from azure.monitor.opentelemetry import configure_azure_monitor
import sys

logger.remove()
logger.add(sys.stdout, format="{time} | {level} - {message}", level="DEBUG")
loaded = False

def init(appconfig: AppConfig) -> None:
        global loaded, tracer, logger
        
        if not appconfig:
            raise('Error initializing logger as appconfig is None')
        
        if not loaded:
             loaded = True
        else:
             return

        if appconfig.appinsightsConnString:
            configure_azure_monitor(
                connection_string=appconfig.appinsightsConnString
            )


def debug(msg):
    logger.debug(msg)

def exception(msg):
    logger.exception(msg)

def exception(msg, **kwargs):
    logger.exception(msg,stack_info=True, exc_info=True)

def warn(msg, **kwargs):
    logger.warning(msg)


