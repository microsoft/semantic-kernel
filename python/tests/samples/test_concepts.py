# Copyright (c) Microsoft. All rights reserved.

import copy

from pytest import mark, param

from samples.concepts.chat_completion.chat_gpt_api import main as chat_gpt_api
from samples.concepts.local_models.lm_studio_chat_completion import main as lm_studio_chat_completion
from samples.concepts.local_models.lm_studio_text_embedding import main as lm_studio_text_embedding
from samples.concepts.local_models.ollama_chat_completion import main as ollama_chat_completion
from tests.samples.test_samples_utils import retry

concepts = [
    # param(
    #     azure_python_code_interpreter_function_calling,
    #     ["print('Hello, World!')", "exit"],
    # ),
    # param(chat_gpt_api_function_calling, ["What is 3+3?", "exit"], id="cht_gpt_api_function_calling"),
    # param(azure_chat_gpt_api, ["Why is the sky blue?", "exit"], id="azure_chat_gpt_api"),
    param(chat_gpt_api, ["What is life?", "exit"], id="chat_gpt_api"),
    # param(chat_streaming, ["Why is the sun hot?", "exit"], id="chat_streaming"),
    # param(openai_logit_bias, [], id="openai_logit_bias"),
    # param(auto_function_invoke_filters, ["What is 3+3?", "exit"], id="auo_function_invoke_filters"),
    # param(function_invocation_filters, ["What is 3+3?", "exit"], id="function_invocation_filters"),
    # param(function_invocation_filters_stream, ["What is 3+3?", "exit"], id="function_invocation_filters_stream"),
    # param(prompt_filters, ["What is the fastest animal?", "exit"], id="prompt_filters"),
    # param(kernel_arguments, [], id="kernel_arguments"),
    # param(grounded, [], id="grounded"),
    # param(azure_cognitive_search_memory, [], id="azure_cognitive_search_memory"),
    # param(memory, ["What are my investments?", "exit"], id="memory"),
    # param(azure_openai_function_calling_stepwise_planner, [], id="azure_openai_function_calling_stepwise_planner"),
    # param(openai_function_calling_stepwise_planner, [], id="openai_function_calling_stepwise_planner"),
    # param(sequential_planner, [], id="sequential_planner"),
    # param(openai_function_calling_with_custom_plugin, [], id="openai_function_calling_with_custom_plugin"),
    # param(
    #     openai_plugin_azure_key_vault,
    #     ["Create a secret with the name 'Foo' and value 'Bar'", "exit"],
    #     id="openai_plugin_azure_key_vault",
    # ),
    # param(openai_plugin_klarna, [], id="openai_plugin_klarna"),
    # param(plugins_from_dir, [], id="plugins_from_dir"),
    # param(azure_chat_gpt_api_handlebars, ["What is 3+3?", "exit"], id="azure_chat_gpt_api_handlebars"),
    # param(azure_chat_gpt_api_jinja2, ["What is 3+3?", "exit"], id="azure_chat_gpt_api_jinja2"),
    # param(configuring_prompts, ["What is my name?", "exit"], id="configuring_prompts"),
    # param(load_yaml_prompt, [], id="load_yaml_prompt"),
    # param(template_language, [], id="template_language"),
    # param(rag_with_text_memory_plugin, [], id="rag_with_text_memory_plugin"),
    # param(bing_search_plugin, [], id="bing_search_plugin"),
    # param(azure_chat_image_input, [], id="azure_chat_image_input"),
    # param(custom_service_selector, [], id="custom_service_selector"),
    param(ollama_chat_completion, ["Why is the sky blue?", "exit"], id="ollama_chat_completion"),
    param(lm_studio_chat_completion, ["Why is the sky blue?", "exit"], id="lm_studio_chat_completion"),
    param(lm_studio_text_embedding, [], id="lm_studio_text_embedding"),
]


@mark.asyncio
@mark.parametrize("func, responses", concepts)
async def test_concepts(func, responses, monkeypatch):
    saved_responses = copy.deepcopy(responses)

    def reset():
        responses.clear()
        responses.extend(saved_responses)

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await retry(lambda: func(), reset=reset)
