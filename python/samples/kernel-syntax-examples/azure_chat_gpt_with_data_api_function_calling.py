# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Tuple

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_function_call,
    get_function_calling_object,
)
from semantic_kernel.core_skills.time_skill import TimeSkill

kernel = sk.Kernel()

# Load Azure OpenAI Settings
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Load Azure OpenAI with data settings
azure_aisearch_datasource = sk_oai.OpenAIChatPromptTemplateWithDataConfig.AzureAISearchDataSource(
    parameters=sk_oai.OpenAIChatPromptTemplateWithDataConfig.AzureAISearchDataSourceParameters(
        **sk.azure_aisearch_settings_from_dot_env_as_dict()
    )
)

azure_chat_with_data_settings = (
    sk_oai.OpenAIChatPromptTemplateWithDataConfig.AzureChatWithDataSettings(
        dataSources=[azure_aisearch_datasource]
    )
)

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

chat_service = sk_oai.AzureChatCompletion(
    deployment_name=deployment,
    api_key=api_key,
    endpoint=endpoint,
    api_version="2023-12-01-preview",
    use_extensions=True,
)
kernel.add_chat_service(
    "chat-gpt",
    chat_service,
)

skills_directory = os.path.join(__file__, "../../../../samples/skills")
# adding skills to the kernel
# the joke skill in the FunSkills is a semantic skill and has the function calling disabled.
kernel.import_semantic_skill_from_directory(skills_directory, "FunSkill")
# the math skill is a core skill and has the function calling enabled.
kernel.import_skill(TimeSkill(), skill_name="time")

# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'SkillName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
prompt_config = (
    sk_oai.OpenAIChatPromptTemplateWithDataConfig.from_completion_parameters(
        max_tokens=2000,
        temperature=0.7,
        top_p=0.8,
        function_call="auto",
        data_source_settings=azure_chat_with_data_settings,
    )
)
prompt_template = OpenAIChatPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message(
    "I am an AI assistant here to answer your questions."
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)

# calling the chat, you could add a overloaded version of the settings here,
# to enable or disable function calling or set the function calling to a specific skill.
# see the openai_function_calling example for how to use this with a unrelated function definition
filter = {"exclude_skill": ["ChatBot"]}
functions = get_function_calling_object(kernel, filter)


async def chat(context: sk.SKContext) -> Tuple[bool, sk.SKContext]:
    try:
        user_input = input("User:> ")
        context.variables["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False, None
    except EOFError:
        print("\n\nExiting chat...")
        return False, None

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False, None

    context = await chat_completion_with_function_call(
        kernel,
        chat_skill_name="ChatBot",
        chat_function_name="Chat",
        context=context,
        functions=functions,
    )
    print(f"Assistant:> {context.result}")
    return True, context


async def main() -> None:
    chatting = True
    context = kernel.create_new_context()
    print(
        "Welcome to the chat bot!\
\n  Type 'exit' to exit.\
\n  Try a time question to see the function calling in action (i.e. what day is it?)."
    )
    while chatting:
        chatting, context = await chat(context)


if __name__ == "__main__":
    asyncio.run(main())
