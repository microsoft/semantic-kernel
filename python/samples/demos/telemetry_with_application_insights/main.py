# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter, AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

from samples.demos.telemetry_with_application_insights.repo_utils import get_sample_plugin_path
from samples.demos.telemetry_with_application_insights.telemetry_sample_settings import TelemetrySampleSettings
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

# Load settings
settings = TelemetrySampleSettings.create()


def set_up_logging():
    log_exporter = AzureMonitorLogExporter(connection_string=settings.connection_string)

    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider()
    # Log processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    # Sets the global default logger provider
    set_logger_provider(logger_provider)

    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Add a filter to the handler to only process records from semantic_kernel.
    handler.addFilter(logging.Filter("semantic_kernel"))
    # Attach the handler to the root logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    logger = logging.getLogger()
    logger.addHandler(handler)
    # Set the logging level to NOTSET to allow all records to be processed by the handler.
    logger.setLevel(logging.NOTSET)


def set_up_tracing():
    trace_exporter = AzureMonitorTraceExporter(connection_string=settings.connection_string)

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider()
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


set_up_logging()
set_up_tracing()


async def main():
    # Initialize the kernel
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="open_ai", ai_model_id="gpt-3.5-turbo"))

    # Add the sample plugin
    if (sample_plugin_path := get_sample_plugin_path()) is None:
        raise FileNotFoundError("Sample plugin path not found.")
    print(f"Sample plugin path: {sample_plugin_path}")
    plugin = kernel.add_plugin(
        plugin_name="WriterPlugin",
        parent_directory=sample_plugin_path,
    )

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main") as current_span:
        print(f"Trace ID: {current_span.get_span_context().trace_id}")

        poem = await kernel.invoke(
            function=plugin["ShortPoem"],
            arguments=KernelArguments(input="Write a poem about John Doe."),
        )
        print(f"Poem:\n{poem}")

        print("\nTranslated poem:")
        async for update in kernel.invoke_stream(
            function=plugin["Translate"],
            arguments=KernelArguments(
                input=poem,
                language="Italian",
            ),
        ):
            print(update[0].content, end="")


if __name__ == "__main__":
    asyncio.run(main())
