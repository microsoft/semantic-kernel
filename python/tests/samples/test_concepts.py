# Copyright (c) Microsoft. All rights reserved.

import copy
import os
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from pytest import mark, param

from samples.concepts.auto_function_calling.chat_completion_with_auto_function_calling import (
    main as chat_completion_with_function_calling,
)
from samples.concepts.auto_function_calling.functions_defined_in_json_prompt import (
    main as function_defined_in_json_prompt,
)
from samples.concepts.auto_function_calling.functions_defined_in_yaml_prompt import (
    main as function_defined_in_yaml_prompt,
)
from samples.concepts.chat_completion.simple_chatbot import main as simple_chatbot
from samples.concepts.chat_completion.simple_chatbot_kernel_function import main as simple_chatbot_kernel_function
from samples.concepts.chat_completion.simple_chatbot_logit_bias import main as simple_chatbot_logit_bias
from samples.concepts.chat_completion.simple_chatbot_streaming import main as simple_chatbot_streaming
from samples.concepts.chat_completion.simple_chatbot_with_image import main as simple_chatbot_with_image
from samples.concepts.filtering.auto_function_invoke_filters import main as auto_function_invoke_filters
from samples.concepts.filtering.function_invocation_filters import main as function_invocation_filters
from samples.concepts.filtering.function_invocation_filters_stream import main as function_invocation_filters_stream
from samples.concepts.filtering.prompt_filters import main as prompt_filters
from samples.concepts.functions.kernel_arguments import main as kernel_arguments
from samples.concepts.grounding.grounded import main as grounded
from samples.concepts.images.image_generation import main as image_generation
from samples.concepts.local_models.lm_studio_chat_completion import main as lm_studio_chat_completion
from samples.concepts.local_models.lm_studio_text_embedding import main as lm_studio_text_embedding
from samples.concepts.local_models.ollama_chat_completion import main as ollama_chat_completion
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
from samples.concepts.plugins.plugins_from_dir import main as plugins_from_dir
from samples.concepts.prompt_templates.azure_chat_gpt_api_handlebars import main as azure_chat_gpt_api_handlebars
from samples.concepts.prompt_templates.azure_chat_gpt_api_jinja2 import main as azure_chat_gpt_api_jinja2
from samples.concepts.prompt_templates.configuring_prompts import main as configuring_prompts
from samples.concepts.prompt_templates.load_yaml_prompt import main as load_yaml_prompt
from samples.concepts.prompt_templates.template_language import main as template_language
from samples.concepts.rag.rag_with_text_memory_plugin import main as rag_with_text_memory_plugin
from samples.concepts.search.bing_search_plugin import main as bing_search_plugin
from samples.concepts.service_selector.custom_service_selector import main as custom_service_selector
from samples.getting_started_with_agents.step1_agent import main as step1_agent
from samples.getting_started_with_agents.step2_plugins import main as step2_plugins
from samples.getting_started_with_agents.step3_chat import main as step3_chat
from samples.getting_started_with_agents.step7_assistant import main as step7_assistant
from tests.utils import retry

# These environment variable names are used to control which samples are run during integration testing.
# This has to do with the setup of the tests and the services they depend on.
COMPLETIONS_CONCEPT_SAMPLE = "COMPLETIONS_CONCEPT_SAMPLE"
MEMORY_CONCEPT_SAMPLE = "MEMORY_CONCEPT_SAMPLE"

concepts = [
    param(
        simple_chatbot,
        ["Why is the sky blue in one sentence?", "exit"],
        id="simple_chatbot",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        simple_chatbot_streaming,
        ["Why is the sky blue in one sentence?", "exit"],
        id="simple_chatbot_streaming",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        simple_chatbot_with_image,
        ["exit"],
        id="simple_chatbot_with_image",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        simple_chatbot_logit_bias,
        ["Who has the most career points in NBA history?", "exit"],
        id="simple_chatbot_logit_bias",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        simple_chatbot_kernel_function,
        ["Why is the sky blue in one sentence?", "exit"],
        id="simple_chatbot_kernel_function",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        chat_completion_with_function_calling,
        ["What is 3+3?", "exit"],
        id="chat_completion_with_function_calling",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        auto_function_invoke_filters,
        ["What is 3+3?", "exit"],
        id="auto_function_invoke_filters",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        function_invocation_filters,
        ["What is 3+3?", "exit"],
        id="function_invocation_filters",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        function_invocation_filters_stream,
        ["What is 3+3?", "exit"],
        id="function_invocation_filters_stream",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        prompt_filters,
        ["What is the fastest animal?", "exit"],
        id="prompt_filters",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        kernel_arguments,
        [],
        id="kernel_arguments",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        grounded,
        [],
        id="grounded",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        azure_openai_function_calling_stepwise_planner,
        [],
        id="azure_openai_function_calling_stepwise_planner",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        openai_function_calling_stepwise_planner,
        [],
        id="openai_function_calling_stepwise_planner",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        sequential_planner,
        [],
        id="sequential_planner",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        openai_function_calling_with_custom_plugin,
        [],
        id="openai_function_calling_with_custom_plugin",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        plugins_from_dir,
        [],
        id="plugins_from_dir",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        azure_chat_gpt_api_handlebars,
        ["What is 3+3?", "exit"],
        id="azure_chat_gpt_api_handlebars",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        azure_chat_gpt_api_jinja2,
        ["What is 3+3?", "exit"],
        id="azure_chat_gpt_api_jinja2",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        configuring_prompts,
        ["What is my name?", "exit"],
        id="configuring_prompts",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        load_yaml_prompt,
        [],
        id="load_yaml_prompt",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        template_language,
        [],
        id="template_language",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        azure_cognitive_search_memory,
        [],
        id="azure_cognitive_search_memory",
        marks=pytest.mark.skipif(os.getenv(MEMORY_CONCEPT_SAMPLE, None) is None, reason="Not running memory samples."),
    ),
    param(
        memory,
        ["What are my investments?", "exit"],
        id="memory",
        marks=pytest.mark.skipif(os.getenv(MEMORY_CONCEPT_SAMPLE, None) is None, reason="Not running memory samples."),
    ),
    param(rag_with_text_memory_plugin, [], id="rag_with_text_memory_plugin"),
    param(
        bing_search_plugin,
        [],
        id="bing_search_plugin",
        marks=pytest.mark.skip(reason="Flaky test due to Azure OpenAI content policy"),
    ),
    param(
        custom_service_selector,
        [],
        id="custom_service_selector",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        function_defined_in_json_prompt,
        ["What is 3+3?", "exit"],
        id="function_defined_in_json_prompt",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        function_defined_in_yaml_prompt,
        ["What is 3+3?", "exit"],
        id="function_defined_in_yaml_prompt",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        step1_agent,
        [],
        id="step1_agent",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        step2_plugins,
        [],
        id="step2_agent_plugins",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        step3_chat,
        [],
        id="step3_chat",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        step7_assistant,
        [],
        id="step7_assistant",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
    param(
        ollama_chat_completion,
        ["Why is the sky blue?", "exit"],
        id="ollama_chat_completion",
        marks=pytest.mark.skip(reason="Need to set up Ollama locally. Check out the module for more details."),
    ),
    param(
        lm_studio_chat_completion,
        ["Why is the sky blue?", "exit"],
        id="lm_studio_chat_completion",
        marks=pytest.mark.skip(reason="Need to set up LM Studio locally. Check out the module for more details."),
    ),
    param(
        lm_studio_text_embedding,
        [],
        id="lm_studio_text_embedding",
        marks=pytest.mark.skip(reason="Need to set up LM Studio locally. Check out the module for more details."),
    ),
    param(
        image_generation,
        [],
        id="image_generation",
        marks=pytest.mark.skipif(
            os.getenv(COMPLETIONS_CONCEPT_SAMPLE, None) is None, reason="Not running completion samples."
        ),
    ),
]


@mark.parametrize("sample, responses", concepts)
async def test_concepts(sample: Callable[..., Awaitable[Any]], responses: list[str], monkeypatch):
    saved_responses = copy.deepcopy(responses)

    def reset():
        responses.clear()
        responses.extend(saved_responses)

    monkeypatch.setattr("builtins.input", lambda _: responses.pop(0))
    await retry(sample, retries=3, reset=reset)
