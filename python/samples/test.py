from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import ChatCompletions, SystemMessage, UserMessage
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.identity import DefaultAzureCredential

from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings

azure_openai_settings = AzureOpenAISettings.create()
deployment_name = azure_openai_settings.chat_deployment_name
endpoint = azure_openai_settings.endpoint


async def complete():
    async with ChatCompletionsClient(
        endpoint=f'{str(endpoint).strip("/")}/openai/deployments/{deployment_name}',
        credential=DefaultAzureCredential(),
        credential_scopes=["https://cognitiveservices.azure.com/.default"],
        api_version=DEFAULT_AZURE_API_VERSION,
    ) as client:
        AIInferenceInstrumentor().instrument()
        response: ChatCompletions = await client.complete(
            messages=[
                SystemMessage(content="You are a helpful assistant."),
                UserMessage(content="How many feet are in a mile?"),
            ]
        )
        print(response)
        AIInferenceInstrumentor().uninstrument()


if __name__ == "__main__":
    import asyncio

    asyncio.run(complete())
