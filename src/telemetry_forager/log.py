import logging
#from loguru import logger
from config import AppConfig
# from azure.monitor.opentelemetry import configure_azure_monitor
from opencensus.ext.azure.log_exporter import AzureLogHandler
# import sys  

#logger.remove()
# logger.add(sys.stdout, format="{time} | {level} - {message}", level="DEBUG")
loaded = False
logger = None


def init(appconfig: AppConfig) -> None:
        #global loaded, tracer, logger

        global loaded, logger

        if not appconfig:
            raise('Error initializing logger as appconfig is None')
        
        if not loaded:
             loaded = True
        else:
             return

        # if appconfig.appinsightsConnString:
        #     configure_azure_monitor(
        #         connection_string=appconfig.appinsightsConnString
        #     )
        azure_handler = AzureLogHandler(connection_string=appconfig.appinsightsConnString)
        azure_handler.setLevel(logging.DEBUG)
        logger = logging.getLogger()
        logger.propagate = False
        if(azure_handler not in logger.handlers):
            logger.addHandler(azure_handler)


def debug(msg):
    logger.debug(msg)

def exception(msg):
    logger.error(msg)

def exception(msg, **kwargs):
    logger.error(msg,stack_info=True, exc_info=True)

def warn(msg, **kwargs):
    logger.warning(msg)


