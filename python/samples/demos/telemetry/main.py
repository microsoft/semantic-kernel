# Copyright (c) Microsoft. All rights reserved.

import argparse
import asyncio
import logging
from typing import Literal

from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorMetricExporter,
    AzureMonitorTraceExporter,
)
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import DropAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import set_tracer_provider
from opentelemetry.trace.span import format_trace_id

from samples.demos.telemetry.scenarios import run_ai_service, run_auto_function_invocation, run_kernel_function
from samples.demos.telemetry.telemetry_sample_settings import TelemetrySampleSettings

# Load settings
settings = TelemetrySampleSettings()

# Create a resource to represent the service/sample
resource = Resource.create({ResourceAttributes.SERVICE_NAME: "TelemetryExample"})

# Define the scenarios that can be run
SCENARIOS = ["ai_service", "kernel_function", "auto_function_invocation", "all"]


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
    if settings.connection_string:
        exporters.append(AzureMonitorLogExporter(connection_string=settings.connection_string))
    if settings.otlp_endpoint:
        exporters.append(OTLPLogExporter(endpoint=settings.otlp_endpoint))
    if not exporters:
        exporters.append(ConsoleLogExporter())

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


def set_up_tracing():
    exporters = []
    if settings.connection_string:
        exporters.append(AzureMonitorTraceExporter(connection_string=settings.connection_string))
    if settings.otlp_endpoint:
        exporters.append(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
    if not exporters:
        exporters.append(ConsoleSpanExporter())

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    for exporter in exporters:
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def set_up_metrics():
    exporters = []
    if settings.connection_string:
        exporters.append(AzureMonitorMetricExporter(connection_string=settings.connection_string))
    if settings.otlp_endpoint:
        exporters.append(OTLPMetricExporter(endpoint=settings.otlp_endpoint))
    if not exporters:
        exporters.append(ConsoleMetricExporter())

    # Initialize a metric provider for the application. This is a factory for creating meters.
    metric_readers = [
        PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000) for metric_exporter in exporters
    ]
    meter_provider = MeterProvider(
        metric_readers=metric_readers,
        resource=resource,
        views=[
            # Dropping all instrument names except for those starting with "semantic_kernel"
            View(instrument_name="*", aggregation=DropAggregation()),
            View(instrument_name="semantic_kernel*"),
        ],
    )
    # Sets the global default meter provider
    set_meter_provider(meter_provider)


async def main(scenario: Literal["ai_service", "kernel_function", "auto_function_invocation", "all"] = "all"):
    # Set up the providers
    # This must be done before any other telemetry calls
    set_up_logging()
    set_up_tracing()
    set_up_metrics()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main") as current_span:
        print(f"Trace ID: {format_trace_id(current_span.get_span_context().trace_id)}")

        stream = False

        # Scenarios where telemetry is collected in the SDK, from the most basic to the most complex.
        if scenario == "ai_service" or scenario == "all":
            await run_ai_service(stream)
        if scenario == "kernel_function" or scenario == "all":
            await run_kernel_function(stream)
        if scenario == "auto_function_invocation" or scenario == "all":
            await run_auto_function_invocation(stream)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "--scenario",
        type=str,
        choices=SCENARIOS,
        default="all",
        help="The scenario to run. Default is all.",
    )

    args = arg_parser.parse_args()

    asyncio.run(main(args.scenario))
