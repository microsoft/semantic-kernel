# Copyright (c) Microsoft. All rights reserved.

from functools import partial, reduce
from typing import Any

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion import GoogleAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_completion import VertexAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings import HuggingFacePromptExecutionSettings
from semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion import HuggingFaceTextCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import AzureTextCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents import TextContent
from tests.integration.completions.test_utils import retry


def setup(
    kernel: Kernel,
    service: str,
    execution_settings_kwargs: dict[str, Any],
    services: dict[str, tuple[TextCompletionClientBase, type[PromptExecutionSettings]]],
):
    kernel.add_service(services[service][0])
    kernel.add_function(
        function_name="text",
        plugin_name="text",
        prompt="If someone asks how you are, always include the word 'well', "
        "if you get a direct question, answer the question. {{$input}}",
        prompt_execution_settings=services[service][1](**execution_settings_kwargs),
    )


@pytest.fixture(scope="module")
def services() -> dict[str, tuple[ChatCompletionClientBase, type[PromptExecutionSettings]]]:
    return {
        "openai": (OpenAITextCompletion(), OpenAITextPromptExecutionSettings),
        "azure": (AzureTextCompletion(), OpenAITextPromptExecutionSettings),
        "hf_t2t": (
            HuggingFaceTextCompletion(
                service_id="patrickvonplaten/t5-tiny-random",
                ai_model_id="patrickvonplaten/t5-tiny-random",
                task="text2text-generation",
            ),
            HuggingFacePromptExecutionSettings,
        ),
        "hf_summ": (
            HuggingFaceTextCompletion(
                service_id="jotamunz/billsum_tiny_summarization",
                ai_model_id="jotamunz/billsum_tiny_summarization",
                task="summarization",
            ),
            HuggingFacePromptExecutionSettings,
        ),
        "hf_gen": (
            HuggingFaceTextCompletion(
                service_id="HuggingFaceM4/tiny-random-LlamaForCausalLM",
                ai_model_id="HuggingFaceM4/tiny-random-LlamaForCausalLM",
                task="text-generation",
            ),
            HuggingFacePromptExecutionSettings,
        ),
        "google_ai": (GoogleAITextCompletion(), GoogleAITextPromptExecutionSettings),
        "vertex_ai": (VertexAITextCompletion(), VertexAITextPromptExecutionSettings),
    }


pytestmark = pytest.mark.parametrize(
    "service, execution_settings_kwargs, inputs, outputs",
    [
        pytest.param(
            "openai",
            {},
            ["Repeat the word Hello"],
            ["Hello"],
            id="openai_text_input",
        ),
        pytest.param(
            "azure",
            {},
            ["Repeat the word Hello"],
            ["Hello"],
            id="azure_text_input",
        ),
        pytest.param(
            "hf_t2t",
            {},
            ["translate English to Dutch: Hello"],
            [""],
            id="hf_t2",
        ),
        pytest.param(
            "hf_summ",
            {},
            [
                """Summarize: Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males."""
            ],
            ["whale"],
            id="hf_summ",
        ),
        pytest.param(
            "hf_gen",
            {},
            ["Hello, I like sleeping and "],
            [""],
            id="hf_gen",
        ),
        pytest.param(
            "google_ai",
            {},
            ["Repeat the word Hello"],
            ["Hello"],
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_text_input",
        ),
        pytest.param(
            "vertex_ai",
            {},
            ["Repeat the word Hello"],
            ["Hello"],
            id="vertex_ai_text_input",
        ),
    ],
)


@pytest.mark.asyncio(scope="module")
async def test_text_completion(
    kernel: Kernel,
    service: str,
    execution_settings_kwargs: dict[str, Any],
    inputs: list[str],
    outputs: list[str],
    services: dict[str, tuple[TextCompletionClientBase, type[PromptExecutionSettings]]],
):
    setup(kernel, service, execution_settings_kwargs, services)
    for message, output in zip(inputs, outputs):
        await retry(partial(execute_invoke, kernel=kernel, input=message, output=output, stream=False), retries=5)


@pytest.mark.asyncio(scope="module")
async def test_streaming_text_completion(
    kernel: Kernel,
    service: str,
    execution_settings_kwargs: dict[str, Any],
    inputs: list[str],
    outputs: list[str],
    services: dict[str, tuple[ChatCompletionClientBase, type[PromptExecutionSettings]]],
):
    setup(kernel, service, execution_settings_kwargs, services)
    for message, output in zip(inputs, outputs):
        await retry(partial(execute_invoke, kernel=kernel, input=message, output=output, stream=True), retries=5)


async def execute_invoke(kernel: Kernel, input: str, output: str, stream: bool) -> None:
    if stream:
        invocation = kernel.invoke_stream(function_name="text", plugin_name="text", input=input)
        parts = [part[0] async for part in invocation]
        if parts:
            response = reduce(lambda p, r: p + r, parts)
        else:
            raise AssertionError("No response")
    else:
        invocation = await kernel.invoke(function_name="text", plugin_name="text", input=input)
        assert invocation is not None
        response = invocation.value[0]
    print(response)
    if isinstance(response, TextContent):
        assert response.text is not None
        assert output in response.text
        return
    raise AssertionError(f"Unexpected output: response: {invocation}, type: {type(invocation)}")
