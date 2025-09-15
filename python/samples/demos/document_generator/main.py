# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from samples.demos.document_generator.agents.code_validation_agent import CodeValidationAgent
from samples.demos.document_generator.agents.content_creation_agent import ContentCreationAgent
from samples.demos.document_generator.agents.user_agent import UserAgent
from samples.demos.document_generator.custom_selection_strategy import CustomSelectionStrategy
from samples.demos.document_generator.custom_termination_strategy import CustomTerminationStrategy
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.contents import AuthorRole, ChatMessageContent

"""
Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.
Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python
Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""

TASK = """
Create a blog post to share technical details about the Semantic Kernel AI connectors.
The content of the blog post should include the following:
1. What are AI connectors in Semantic Kernel?
2. How do people use AI connectors in Semantic Kernel?
3. How do devs create custom AI connectors in Semantic Kernel?
    - Include a walk through of creating a custom AI connector. 
      The connector may not connect to a real service, but should demonstrate the process.
    - Include a sample on how to use the connector.
    - If a reader follows the walk through and the sample, they should be able to run the connector.


Here is the file that contains the source code for the base class of the AI connectors:
semantic_kernel/connectors/ai/chat_completion_client_base.py
semantic_kernel/services/ai_service_client_base.py

Here are some files containing the source code that may be useful:
semantic_kernel/connectors/ai/ollama/services/ollama_chat_completion.py
semantic_kernel/connectors/ai/open_ai/services/open_ai_chat_completion_base.py
semantic_kernel/contents/chat_history.py

If you want to reference the implementations of other AI connectors, you can find them under the following directory:
semantic_kernel/connectors/ai
"""

load_dotenv()
AZURE_APP_INSIGHTS_CONNECTION_STRING = os.getenv("AZURE_APP_INSIGHTS_CONNECTION_STRING")

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "Document Generator"})


def set_up_tracing():
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import set_tracer_provider

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(AzureMonitorTraceExporter(connection_string=AZURE_APP_INSIGHTS_CONNECTION_STRING))
    )
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def set_up_logging():
    from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(AzureMonitorLogExporter(connection_string=AZURE_APP_INSIGHTS_CONNECTION_STRING))
    )
    # Sets the global default logger provider
    set_logger_provider(logger_provider)

    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Attach the handler to the root logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


async def main():
    if AZURE_APP_INSIGHTS_CONNECTION_STRING:
        set_up_tracing()
        set_up_logging()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main"):
        agents = [
            ContentCreationAgent(),
            UserAgent(),
            CodeValidationAgent(),
        ]

        group_chat = AgentGroupChat(
            agents=agents,
            termination_strategy=CustomTerminationStrategy(agents=agents),
            selection_strategy=CustomSelectionStrategy(),
        )
        await group_chat.add_chat_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=TASK.strip(),
            )
        )

        async for response in group_chat.invoke():
            print(f"==== {response.name} just responded ====")
            # print(response.content)

        content_history: list[ChatMessageContent] = []
        async for message in group_chat.get_chat_messages(agent=agents[0]):
            if message.name == agents[0].name:
                # The chat history contains responses from other agents.
                content_history.append(message)
        # The chat history is in descending order.
        print("Final content:")
        print(content_history[0].content)


if __name__ == "__main__":
    asyncio.run(main())
