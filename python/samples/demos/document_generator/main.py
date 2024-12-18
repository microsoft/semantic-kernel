# Copyright (c) Microsoft. All rights reserved.

import asyncio

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from samples.demos.document_generator.agents.code_validation_agent import CodeValidationAgent
from samples.demos.document_generator.agents.content_creation_agent import ContentCreationAgent
from samples.demos.document_generator.agents.proofread_agent import ProofreadAgent
from samples.demos.document_generator.custom_termination_strategy import CustomTerminationStrategy
from semantic_kernel.agents.group_chat.agent_group_chat import AgentGroupChat
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

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

Here are some files containing the source code that may be useful:
semantic_kernel/connectors/ai/ollama/services/ollama_chat_completion.py
semantic_kernel/connectors/ai/chat_completion_client_base.py
"""

AZURE_AI_INFERENCE_SERVICE_ID = "azure_chat_completion"
AZURE_APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=c9eb6284-0ee7-42fe-b17c-84d693d7ec8d;IngestionEndpoint=https://southcentralus-3.in.applicationinsights.azure.com/;LiveEndpoint=https://southcentralus.livediagnostics.monitor.azure.com/;ApplicationId=3927ed4d-8bd3-4d20-aa89-a797e7a3ddbf"

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


async def main():
    set_up_tracing()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main"):
        agents = [
            ContentCreationAgent(),
            ProofreadAgent(),
            CodeValidationAgent(),
        ]

        group_chat = AgentGroupChat(
            agents=agents,
            termination_strategy=CustomTerminationStrategy(agents=agents),
        )
        await group_chat.add_chat_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=TASK,
            )
        )

        async for content in group_chat.invoke():
            print(content)


if __name__ == "__main__":
    asyncio.run(main())
