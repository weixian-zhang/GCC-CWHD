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

        console_handler = logging.StreamHandler()

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(azure_handler)
        logger.addHandler(console_handler)

        # disable uvicorn logs
        # logging.getLogger("uvicorn.error").handlers = []
        # logging.getLogger("uvicorn.error").propagate = False

        # logging.getLogger("uvicorn.access").handlers = []
        # logging.getLogger("uvicorn.access").propagate = False

        # logging.getLogger("uvicorn.asgi").handlers = []
        # logging.getLogger("uvicorn.asgi").propagate = True

        # http client related logs level t
        az_http_logging = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
        az_http_logging.setLevel(logging.ERROR)

        # all azure library log level error only
        all_azure_logger = logger = logging.getLogger('azure')
        all_azure_logger.setLevel(logging.ERROR)


def debug(msg):
    logger.debug(msg)

def exception(msg):
    logger.error(msg)

def exception(msg, **kwargs):
    logger.error(msg,stack_info=True, exc_info=True)

def warn(msg, **kwargs):
    logger.warning(msg)


