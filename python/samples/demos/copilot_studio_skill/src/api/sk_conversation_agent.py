# Copyright (c) Microsoft. All rights reserved.

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from config import config
from openai import AsyncAzureOpenAI

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")


def create_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        azure_deployment=config.AZURE_OPENAI_MODEL,
        azure_ad_token_provider=token_provider,
        api_version=config.AZURE_OPENAI_API_VERSION,
    )


def create_service(service_id: str = "default"):
    return AzureChatCompletion(
        deployment_name=config.AZURE_OPENAI_MODEL,
        async_client=create_client(),
        service_id=service_id,
    )


agent = ChatCompletionAgent(
    service=create_service(),
    name="ChatAgent",
    instructions="You invent jokes to have a fun conversation with the user.",
)
