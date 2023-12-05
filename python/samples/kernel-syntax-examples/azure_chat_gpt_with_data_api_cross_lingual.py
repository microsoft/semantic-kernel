# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.models.chat.azure_chat_with_data_settings import (
    AzureAISearchDataSourceParameters,
    AzureChatWithDataSettings,
    DataSourceType,
)

kernel = sk.Kernel()

# Load Azure OpenAI Settings
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Load Azure OpenAI with data settings
azure_chat_with_data_settings = AzureChatWithDataSettings(
    data_source_type=DataSourceType.AZURE_AI_SEARCH,
    data_source_parameters=AzureAISearchDataSourceParameters(
        **sk.azure_aisearch_datasource_settings_from_dot_env_as_dict()
    ),
)

# Set index language
azure_chat_with_data_settings.data_source_parameters.indexLanguage = "en"

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.


kernel.add_chat_service(
    "chat-gpt",
    sk_oai.AzureChatCompletionWithData(
        deployment_name=deployment,
        endpoint=endpoint,
        api_key=api_key,
        api_version="2023-12-01-preview",
        data_source_settings=azure_chat_with_data_settings,
    ),
)

prompt_config = sk.PromptTemplateWithDataConfig.from_completion_parameters(
    max_tokens=2000, temperature=0.7, top_p=0.8, inputLanguage="fr", outputLanguage="de"
)

prompt_template = sk.ChatWithDataPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)

prompt_template.add_user_message("Bonjour!")
prompt_template.add_assistant_message(
    "Ich freue mich, euch die Geschichte von Emily und David erzählen zu können. Was möchten Sie wissen?"
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)


async def chat() -> bool:
    context_vars = sk.ContextVariables()
    print(
        "Welcome to the chat bot!\
    \n  Type 'exit' to exit.\
    \n  Type your question in French, and see the response in German. \
    \n  For example, 'Où Emily et David se sont-ils rencontrés?'"
    )
    try:
        user_input = input("User:> ")
        context_vars["user_input"] = user_input
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
    # answer = await kernel.run_async(chat_function, input_vars=context_vars)
    # print(f"Assistant:> {answer}")

    answer = kernel.run_stream_async(chat_function, input_vars=context_vars)
    print("Assistant:> ", end="")
    async for message in answer:
        print(message, end="")
    print("\n")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
