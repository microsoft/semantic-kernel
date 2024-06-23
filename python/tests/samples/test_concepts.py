# Copyright (c) Microsoft. All rights reserved.

from pytest import mark, param

from samples.concepts.auto_function_calling.azure_python_code_interpreter_function_calling import (
    main as azure_python_code_interpreter_function_calling,
)
from samples.concepts.auto_function_calling.chat_gpt_api_function_calling import main as chat_gpt_api_function_calling
from samples.concepts.chat_completion.azure_chat_gpt_api import main as azure_chat_gpt_api
from samples.concepts.chat_completion.azure_chat_image_input import main as azure_chat_image_input
from samples.concepts.chat_completion.chat_gpt_api import main as chat_gpt_api
from samples.concepts.chat_completion.chat_streaming import main as chat_streaming
from samples.concepts.chat_completion.openai_logit_bias import main as openai_logit_bias
from samples.concepts.filtering.auto_function_invoke_filters import main as auto_function_invoke_filters
from samples.concepts.filtering.function_invocation_filters import main as function_invocation_filters
from samples.concepts.filtering.function_invocation_filters_stream import main as function_invocation_filters_stream
from samples.concepts.filtering.prompt_filters import main as prompt_filters
from samples.concepts.functions.kernel_arguments import main as kernel_arguments
from samples.concepts.grounding.grounded import main as grounded
from samples.concepts.memory.azure_cognitive_search_memory import main as azure_cognitive_search_memory
from samples.concepts.memory.memory import main as memory
from samples.concepts.planners.azure_openai_function_calling_stepwise_planner import (
    main as azure_openai_function_calling_stepwise_planner,
)
from samples.concepts.planners.openai_function_calling_stepwise_planner import (
    main as openai_function_calling_stepwise_planner,
)
from samples.concepts.planners.sequential_planner import main as sequential_planner
from samples.concepts.plugins.openai_function_calling_with_custom_plugin import (
    main as openai_function_calling_with_custom_plugin,
)
from samples.concepts.plugins.openai_plugin_azure_key_vault import main as openai_plugin_azure_key_vault
from samples.concepts.plugins.openai_plugin_klarna import main as openai_plugin_klarna
from samples.concepts.plugins.plugins_from_dir import main as plugins_from_dir
from samples.concepts.prompt_templates.azure_chat_gpt_api_handlebars import main as azure_chat_gpt_api_handlebars
from samples.concepts.prompt_templates.azure_chat_gpt_api_jinja2 import main as azure_chat_gpt_api_jinja2
from samples.concepts.prompt_templates.configuring_prompts import main as configuring_prompts
from samples.concepts.prompt_templates.load_yaml_prompt import main as load_yaml_prompt
from samples.concepts.prompt_templates.template_language import main as template_language
from samples.concepts.rag.rag_with_text_memory_plugin import main as rag_with_text_memory_plugin
from samples.concepts.search.bing_search_plugin import main as bing_search_plugin
from samples.concepts.service_selector.custom_service_selector import main as custom_service_selector
from tests.samples.test_samples_utils import retry

concepts = [
    param(
        azure_python_code_interpreter_function_calling,
        ["print('Hello, World!')", "exit"],
        id="azure_python_code_interpreter_function_calling",
    ),
    param(chat_gpt_api_function_calling, ["What is 3+3?", "exit"], id="cht_gpt_api_function_calling"),
    param(azure_chat_gpt_api, ["Why is the sky blue?", "exit"], id="azure_chat_gpt_api"),
    param(chat_gpt_api, ["What is life?", "exit"], id="chat_gpt_api"),
    param(chat_streaming, ["Why is the sun hot?", "exit"], id="chat_streaming"),
    param(openai_logit_bias, [], id="openai_logit_bias"),
    param(auto_function_invoke_filters, ["What is 3+3?", "exit"], id="auo_function_invoke_filters"),
    param(function_invocation_filters, ["What is 3+3?", "exit"], id="function_invocation_filters"),
    param(function_invocation_filters_stream, ["What is 3+3?", "exit"], id="function_invocation_filters_stream"),
    param(prompt_filters, ["What is the fastest animal?", "exit"], id="prompt_filters"),
    param(kernel_arguments, [], id="kernel_arguments"),
    param(grounded, [], id="grounded"),
    param(azure_cognitive_search_memory, [], id="azure_cognitive_search_memory"),
    param(memory, ["What are my investments?", "exit"], id="memory"),
    param(azure_openai_function_calling_stepwise_planner, [], id="azure_openai_function_calling_stepwise_planner"),
    param(openai_function_calling_stepwise_planner, [], id="openai_function_calling_stepwise_planner"),
    param(sequential_planner, [], id="sequential_planner"),
    param(openai_function_calling_with_custom_plugin, [], id="openai_function_calling_with_custom_plugin"),
    param(
        openai_plugin_azure_key_vault,
        ["Create a secret with the name 'Foo' and value 'Bar'", "exit"],
        id="openai_plugin_azure_key_vault",
    ),
    param(openai_plugin_klarna, [], id="openai_plugin_klarna"),
    param(plugins_from_dir, [], id="plugins_from_dir"),
    param(azure_chat_gpt_api_handlebars, ["What is 3+3?", "exit"], id="azure_chat_gpt_api_handlebars"),
    param(azure_chat_gpt_api_jinja2, ["What is 3+3?", "exit"], id="azure_chat_gpt_api_jinja2"),
    param(configuring_prompts, ["What is my name?", "exit"], id="configuring_prompts"),
    param(load_yaml_prompt, [], id="load_yaml_prompt"),
    param(template_language, [], id="template_language"),
    param(rag_with_text_memory_plugin, [], id="rag_with_text_memory_plugin"),
    param(bing_search_plugin, [], id="bing_search_plugin"),
    param(azure_chat_image_input, [], id="azure_chat_image_input"),
    param(custom_service_selector, [], id="custom_service_selector"),
]


@mark.asyncio
@mark.parametrize("func, responses", concepts)
async def test_concepts(func, responses, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await retry(lambda: func())
