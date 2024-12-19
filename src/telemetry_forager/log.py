import logging
from loguru import logger
from config import AppConfig
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry import trace
from opentelemetry.trace import (
    SpanKind,
    get_tracer_provider,
    set_tracer_provider,
)
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.propagate import extract
from azure.core.settings import settings
from azure.core.tracing.ext.opentelemetry_span import OpenTelemetrySpan
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
settings.tracing_implementation = OpenTelemetrySpan
import sys

# tracer = None
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# stream = logging.StreamHandler(sys.stdout)
# logger.addHandler(stream)
logger.remove()
logger.add(sys.stdout, format="{time} | {level} - {message}", level="DEBUG")
# logger.add(sys.stderr, format="{time} | {level} - {message}", level="DEBUG")
loaded = False

def init(appconfig: AppConfig) -> None:
        global loaded, tracer, logger
        
        if not appconfig:
            raise('Error initializing logger as appconfig is None')
        
        if not loaded:
             loaded = True
        else:
             return
        

        # Set up OpenTelemetry tracer
        # disable tracing for now to prevent overlogging. Too noisy disrupts log finding
        # exporter = ConsoleSpanExporter()
        # trace.set_tracer_provider(TracerProvider())
        # trace.get_tracer_provider().add_span_processor(
        #     SimpleSpanProcessor(exporter)
        # )

        if appconfig.appinsightsConnString:
            # azmon_exporter = AzureMonitorTraceExporter.from_connection_string(appconfig.appinsightsConnString)
            
            # trace.get_tracer_provider().add_span_processor(
            #     SimpleSpanProcessor(azmon_exporter)
            # )

            configure_azure_monitor(
                connection_string=appconfig.appinsightsConnString
            )


        #tracer = trace.get_tracer(__name__)


def debug(msg):
    logger.debug(msg)


def exception(msg):
    logger.exception(msg)

def exception(msg, **kwargs):
    logger.exception(msg,stack_info=True, exc_info=True)

def warn(msg, **kwargs):
    logger.warning(msg)

def get_tracer():
     return tracer

