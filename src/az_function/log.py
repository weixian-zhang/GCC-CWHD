import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from config import AppConfig
# from azure.monitor.opentelemetry import configure_azure_monitor
# Import the tracing api from the `opentelemetry` package.
# from opentelemetry import trace



# Get a tracer for the current module.
# tracer = trace.get_tracer(__name__)

#override Azure's root logger to be able to log to console
logger = logging.getLogger('akshay')
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
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
        
        appinsightsExceptionHandler = AzureLogHandler(connection_string=f'InstrumentationKey={appconfig.appinsightsInstrumentationKey}')
        appinsightsExceptionHandler.setLevel(logging.ERROR)
        logger.addHandler(appinsightsExceptionHandler)

        appinsightsWarnHandler = AzureLogHandler(connection_string=f'InstrumentationKey={appconfig.appinsightsInstrumentationKey}')
        appinsightsWarnHandler.setLevel(logging.WARN)
        logger.addHandler(appinsightsWarnHandler)

        # configure_azure_monitor(
        #     connection_string=appconfig.appinsightsConnString
        # )


def debug(msg):
    logger.debug(msg)


def exception(msg):
    logger.exception(msg, exc_info=True)

def exception(msg, **kwargs):

    appinsightsCusomtProps = {'custom_dimensions': {}}
    for k, v in kwargs.items():
        appinsightsCusomtProps['custom_dimensions'][k] = v

    logger.exception(msg, exc_info=True, extra=appinsightsCusomtProps)

def warn(msg, **kwargs):

    appinsightsCusomtProps = {'custom_dimensions': {}}
    for k, v in kwargs.items():
        appinsightsCusomtProps['custom_dimensions'][k] = v

    logger.warn(msg, extra=appinsightsCusomtProps)

# def get_tracer():
#      return tracer

