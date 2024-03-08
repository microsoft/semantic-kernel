# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureAISearchDataSources,
    AzureChatPromptExecutionSettings,
    AzureDataSources,
    AzureEmbeddingDependency,
    ExtraBody,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.utils.settings import (
    azure_aisearch_settings_from_dot_env_as_dict,
    azure_openai_settings_from_dot_env_as_dict,
)

kernel = sk.Kernel()

# Load Azure OpenAI Settings
aoai_settings = azure_openai_settings_from_dot_env_as_dict(include_api_version=True)

# When using data, set use_extensions=True and use the 2023-12-01-preview API version.
chat_service = sk_oai.AzureChatCompletion(
    service_id="chat-gpt",
    use_extensions=True,
    **aoai_settings,
)
kernel.add_service(chat_service)

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

azure_ai_search_settings = azure_aisearch_settings_from_dot_env_as_dict()
az_source = AzureAISearchDataSources(
    indexName=azure_ai_search_settings["indexName"],
    fieldsMapping={
        "titleField": "title",
        "contentFields": ["chunk"],
        "vectorFields": ["vector"],
    },
    embeddingDependency=AzureEmbeddingDependency(type="DeploymentName", deploymentName="text-embedding-ada-002"),
    endpoint=azure_ai_search_settings["endpoint"],
    key=azure_ai_search_settings["key"],
    queryType="vector",
)

# Create the data source settings
req_settings = AzureChatPromptExecutionSettings(
    temperature=0.0,
    maxTokens=1000,
    extra_body=ExtraBody(dataSources=[AzureDataSources(type="AzureCognitiveSearch", parameters=az_source)]),
)

chat_function = kernel.create_function_from_prompt(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
    prompt_execution_settings=req_settings,
)

chat_history = ChatHistory(system_message="You are a assistant, you help users understand the complex world of ...")


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    full_message = None
    print("Assistant:> ", end="")
    async for message in kernel.invoke_stream(chat_function, chat_history=chat_history, user_input=user_input):
        if not isinstance(message, FunctionResult):
            print(str(message[0]), end="")
            full_message = message[0] if not full_message else full_message + message[0]
        else:
            print("something went wrong")
            print(str(message), end="")
    print("")
    if full_message:
        chat_history.add_user_message(user_input)
        if hasattr(full_message, "tool_message"):
            chat_history.add_message(
                AzureChatMessageContent(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            index=0,
                            id="chat_with_your_data",
                            function=FunctionCall(name="chat_with_your_data", arguments=""),
                        )
                    ],
                )
            )
            chat_history.add_tool_message(full_message.tool_message, {"tool_call_id": "chat_with_your_data"})
        if full_message.role is None:
            full_message.role = ChatRole.ASSISTANT
        chat_history.add_message(full_message)
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
