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
    ExtraBody,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.settings import (
    azure_aisearch_settings_from_dot_env_as_dict,
    azure_openai_settings_from_dot_env_as_dict,
)

kernel = sk.Kernel()

# Load Azure OpenAI Settings
aoai_settings = azure_openai_settings_from_dot_env_as_dict()

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

azure_ai_search_settings = azure_aisearch_settings_from_dot_env_as_dict()

# Our example index has fields "source_title", "source_text", "source_url", and "source_file".
# Add fields mapping to the settings to indicate which fields to use for the title, content, URL, and file path.
azure_ai_search_settings["fieldsMapping"] = {
    "titleField": "source_title",
    "urlField": "source_url",
    "contentFields": ["source_text"],
    "filepathField": "source_file",
}

# Create the data source settings
az_source = AzureAISearchDataSources(**azure_ai_search_settings)
az_data = AzureDataSources(type="AzureCognitiveSearch", parameters=az_source)
extra = ExtraBody(dataSources=[az_data])
req_settings = AzureChatPromptExecutionSettings(service_id="default", extra_body=extra)

# When using data, set use_extensions=True and use the 2023-12-01-preview API version.
chat_service = sk_oai.AzureChatCompletion(
    service_id="chat-gpt",
    use_extensions=True,
    **aoai_settings,
)
kernel.add_service(chat_service)

prompt_template_config = PromptTemplateConfig(
    template="{{$chat_history}}{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="chat_history", description="The chat history", is_required=True),
        InputVariable(name="request", description="The user input", is_required=True),
    ],
    execution_settings={"default": req_settings},
)
chat_function = kernel.create_function_from_prompt(
    plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
)

chat_history = ChatHistory()
chat_history.add_system_message("I am an AI assistant here to answer your questions.")


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

    # Non streaming
    # answer = await kernel.run(chat_function, input_vars=context_vars)
    # print(f"Assistant:> {answer}")
    arguments = KernelArguments(chat_history=chat_history, user_input=user_input, execution_settings=req_settings)

    full_message = None
    print("Assistant:> ", end="")
    async for message in kernel.invoke_stream(chat_function, arguments=arguments):
        print(str(message[0]), end="")
        full_message = message[0] if not full_message else full_message + message[0]
    print("\n")

    # The tool message containing cited sources is available in the context
    if full_message:
        chat_history.add_user_message(user_input)
        if hasattr(full_message, "tool_message"):
            chat_history.add_message(
                AzureChatMessageContent(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
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
