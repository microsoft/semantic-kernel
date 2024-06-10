# Copyright (c) Microsoft. All rights reserved.

from pytest import mark

from samples.concepts.auto_function_calling.azure_python_code_interpreter_function_calling import (
    main as azure_python_code_interpreter_function_calling,
)
from samples.concepts.auto_function_calling.chat_gpt_api_function_calling import main as chat_gpt_api_function_calling
from samples.concepts.chat_completion.azure_chat_gpt_api import main as azure_chat_gpt_api
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
from samples.concepts.plugins.azure_python_code_interpreter import main as azure_python_code_interpreter
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


@mark.asyncio
@mark.parametrize(
    "func,responses",
    [
        (azure_python_code_interpreter_function_calling, ["print('Hello, World!')", "exit"]),
        (chat_gpt_api_function_calling, ["What is 3+3?", "exit"]),
        (azure_chat_gpt_api, ["Why is the sky blue?", "exit"]),
        (chat_gpt_api, ["What is life?", "exit"]),
        (chat_streaming, ["Why is the sun hot?", "exit"]),
        (openai_logit_bias, []),
        (auto_function_invoke_filters, ["What is 3+3?", "exit"]),
        (function_invocation_filters, ["What is 3+3?", "exit"]),
        (function_invocation_filters_stream, ["What is 3+3?", "exit"]),
        (prompt_filters, ["What is the fastest animal?", "exit"]),
        (kernel_arguments, []),
        (grounded, []),
        (azure_cognitive_search_memory, []),
        (memory, ["What are my investments?", "exit"]),
        (azure_openai_function_calling_stepwise_planner, []),
        (openai_function_calling_stepwise_planner, []),
        (sequential_planner, []),
        (azure_python_code_interpreter, []),
        (openai_function_calling_with_custom_plugin, []),
        (openai_plugin_azure_key_vault, ["Create a secret with the name 'Foo' and value 'Bar'", "exit"]),
        (openai_plugin_klarna, []),
        (plugins_from_dir, []),
        (azure_chat_gpt_api_handlebars, ["What is 3+3?", "exit"]),
        (azure_chat_gpt_api_jinja2, ["What is 3+3?", "exit"]),
        (configuring_prompts, ["What is my name?", "exit"]),
        (load_yaml_prompt, []),
        (template_language, []),
        (rag_with_text_memory_plugin, []),
        (bing_search_plugin, []),
    ],
    ids=[
        "azure_python_code_interpreter_function_calling",
        "chat_gpt_api_function_calling",
        "azure_chat_gpt_api",
        "chat_gpt_api",
        "chat_streaming",
        "openai_logit_bias",
        "auto_function_invoke_filters",
        "function_invocation_filters",
        "function_invocation_filters_stream",
        "prompt_filters",
        "kernel_arguments",
        "grounded",
        "azure_cognitive_search_memory",
        "memory",
        "azure_openai_function_calling_stepwise_planner",
        "openai_function_calling_stepwise_planner",
        "sequential_planner",
        "azure_python_code_interpreter",
        "openai_function_calling_with_custom_plugin",
        "openai_plugin_azure_key_vault",
        "openai_plugin_klarna",
        "plugins_from_dir",
        "azure_chat_gpt_api_handlebars",
        "azure_chat_gpt_api_jinja2",
        "configuring_prompts",
        "load_yaml_prompt",
        "template_language",
        "rag_with_text_memory_plugin",
        "bing_search_plugin",
    ],
)
async def test_concepts(func, responses, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await func()
