# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.request_settings.azure_chat_request_settings import (
    AzureAISearchDataSources,
    AzureChatRequestSettings,
    AzureDataSources,
    ExtraBody,
)

kernel = sk.Kernel()

# Load Azure OpenAI Settings
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Load Azure AI Search settings
azure_ai_search_settings = sk.azure_aisearch_settings_from_dot_env_as_dict()
# Set index language
azure_ai_search_settings["indexLanguage"] = "en"

# Create the data source settings
az_source = AzureAISearchDataSources(**azure_ai_search_settings)
az_data = AzureDataSources(type="AzureCognitiveSearch", parameters=az_source)
extra = ExtraBody(data_sources=[az_data], input_language="fr", output_language="de")
req_settings = AzureChatRequestSettings(extra_body=extra)
prompt_config = sk.PromptTemplateConfig(execution_settings=req_settings)

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.


chat_service = sk_oai.AzureChatCompletion(
    use_extensions=True,
    deployment_name=deployment,
    api_key=api_key,
    endpoint=endpoint,
    api_version="2023-12-01-preview",
)
kernel.add_chat_service(
    "chat-gpt",
    chat_service,
)

prompt_template = sk.ChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)

prompt_template.add_user_message("Bonjour!")
prompt_template.add_assistant_message(
    "Ich freue mich, euch die Geschichte von Emily und David erzählen zu können. Wie kann ich helfen?"
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)


async def chat() -> bool:
    context_vars = sk.ContextVariables()

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
    # answer = await kernel.run(chat_function, input_vars=context_vars)
    # print(f"Assistant:> {answer}")

    answer = kernel.run_stream(chat_function, input_vars=context_vars)
    print("Assistant:> ", end="")
    async for message in answer:
        print(message, end="")
    print("\n")
    return True


async def main() -> None:
    chatting = True
    print(
        "Welcome to the chat bot!\
    \n  Type 'exit' to exit.\
    \n  Type your question in French, and see the response in German. \
    \n  For example, 'Où Emily et David se sont-ils rencontrés?'"
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
