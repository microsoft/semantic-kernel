# Copyright (c) Microsoft. All rights reserved.

import logging
import os
import sys

from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorTraceExporter,
)
from dotenv import load_dotenv
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import set_tracer_provider

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

load_dotenv()

APPINSIGHTS_CONNECTION_STRING = os.getenv("APPINSIGHTS_CONNECTION_STRING")

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "TravelPlanningSystemDemo"})


def set_up_logging():
    class KernelFilter(logging.Filter):
        """A filter to not process records from semantic_kernel."""

        # These are the namespaces that we want to exclude from logging for the purposes of this demo.
        namespaces_to_exclude: list[str] = [
            "semantic_kernel.functions.kernel_plugin",
            "semantic_kernel.prompt_template.kernel_prompt_template",
        ]

        def filter(self, record):
            return not any([record.name.startswith(namespace) for namespace in self.namespaces_to_exclude])

    exporters = []
    exporters.append(AzureMonitorLogExporter(connection_string=APPINSIGHTS_CONNECTION_STRING))

    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider(resource=resource)
    # Log processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    for log_exporter in exporters:
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    # Sets the global default logger provider
    set_logger_provider(logger_provider)

    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Add filters to the handler to only process records from semantic_kernel.
    handler.addFilter(logging.Filter("semantic_kernel"))
    handler.addFilter(KernelFilter())
    # Attach the handler to the root logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    logger = logging.getLogger()
    logger.addHandler(handler)
    # Set the logging level to NOTSET to allow all records to be processed by the handler.
    logger.setLevel(logging.NOTSET)


class CustomBatchSpanProcessor(BatchSpanProcessor):
    @override
    def on_end(self, span: ReadableSpan):
        if span.name.startswith("agent_runtime"):
            # Skip spans that are part of the agent runtime.
            return
        super().on_end(span)


def set_up_tracing():
    exporters = []
    exporters.append(AzureMonitorTraceExporter(connection_string=APPINSIGHTS_CONNECTION_STRING))

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    for exporter in exporters:
        tracer_provider.add_span_processor(CustomBatchSpanProcessor(exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)
