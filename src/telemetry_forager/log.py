import logging
#from loguru import logger
from config import AppConfig
# from azure.monitor.opentelemetry import configure_azure_monitor
from opencensus.ext.azure.log_exporter import AzureLogHandler
import sys  

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

        # http client related logs level t
        logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

        # all azure library log level error only
        az_logger = logging.getLogger('azure.storage')
        az_logger.setLevel(logging.ERROR)
        az_logger.addHandler(logging.StreamHandler(stream=sys.stdout))

        azure_handler = AzureLogHandler(connection_string=appconfig.appinsightsConnString)
        azure_handler.setLevel(level=logging.ERROR)
        console_handler = logging.StreamHandler()

        logger = logging.getLogger('default_logger')
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(azure_handler)
        logger.addHandler(console_handler)



def debug(msg):
    logger.debug(msg)

def exception(msg):
    logger.error(msg)

def exception(msg, **kwargs):
    logger.error(msg,stack_info=True, exc_info=True)

def warn(msg, **kwargs):
    logger.warning(msg)


