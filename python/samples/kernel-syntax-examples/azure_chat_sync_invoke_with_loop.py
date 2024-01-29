# Copyright (c) Microsoft. All rights reserved.


import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import PromptTemplateConfig
from semantic_kernel.semantic_functions.semantic_function_config import SemanticFunctionConfig
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict


# This example shows how to use the AzureChatCompletion semantic function to invoke the
# Azure OpenAI chat API synchronously. Underneath the sync invoke is an async invoke, so
# this is an example/test that the underlying functionality is working properly.
def azure_open_ai_sync_invoke():
    kernel = sk.Kernel()
    aoai_settings_dict = azure_openai_settings_from_dot_env_as_dict(include_deployment=True, include_api_version=True)
    kernel.add_chat_service("chat_completion", AzureChatCompletion(**aoai_settings_dict))
    prompt_config = PromptTemplateConfig()
    prompt_template = ChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)

    function_config = SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("testfn", "testfn", function_config)

    texts = ["Tell me about the stars", "Tell me about the ocean.", "Tell me about the forest."]

    for i in range(3):
        text = f"Explain the following in one sentence: {texts[i]}."
        context = kernel.create_new_context()
        context["user_input"] = text
        print(f"User input: {text}")
        result = chat_function.invoke(context=context)
        print(result.result)


if __name__ == "__main__":
    azure_open_ai_sync_invoke()
