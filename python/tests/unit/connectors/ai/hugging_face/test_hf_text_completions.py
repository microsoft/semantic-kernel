# Copyright (c) Microsoft. All rights reserved.

from threading import Thread
from unittest.mock import MagicMock, Mock, patch

import pytest
from transformers import AutoTokenizer, TextIteratorStreamer

from semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion import HuggingFaceTextCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import KernelInvokeException, ServiceResponseException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.parametrize(
    ("model_name", "task", "input_str"),
    [
        (
            "patrickvonplaten/t5-tiny-random",
            "text2text-generation",
            "translate English to Dutch: Hello, how are you?",
        ),
        (
            "jotamunz/billsum_tiny_summarization",
            "summarization",
            """
        Summarize: Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males.
    """,
        ),
        ("HuggingFaceM4/tiny-random-LlamaForCausalLM", "text-generation", "Hello, I like sleeping and "),
    ],
    ids=["text2text-generation", "summarization", "text-generation"],
)
async def test_text_completion(model_name, task, input_str):
    kernel = Kernel()

    ret = {"summary_text": "test"} if task == "summarization" else {"generated_text": "test"}
    mock_pipeline = Mock(return_value=ret)

    # Configure LLM service
    with patch("semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline") as patched_pipeline:
        patched_pipeline.return_value = mock_pipeline
        service = HuggingFaceTextCompletion(service_id=model_name, ai_model_id=model_name, task=task)
        kernel.add_service(
            service=service,
        )

        exec_settings = PromptExecutionSettings(service_id=model_name, extension_data={"max_new_tokens": 25})

        # Define semantic function using SK prompt template language
        prompt = "{{$input}}"

        prompt_template_config = PromptTemplateConfig(template=prompt, execution_settings=exec_settings)

        kernel.add_function(
            prompt_template_config=prompt_template_config,
            function_name="TestFunction",
            plugin_name="TestPlugin",
            prompt_execution_settings=exec_settings,
        )

        arguments = KernelArguments(input=input_str)

        await kernel.invoke(function_name="TestFunction", plugin_name="TestPlugin", arguments=arguments)
        assert mock_pipeline.call_args.args[0] == input_str


async def test_text_completion_throws():
    kernel = Kernel()

    model_name = "patrickvonplaten/t5-tiny-random"
    task = "text2text-generation"
    input_str = "translate English to Dutch: Hello, how are you?"

    with patch("semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline") as patched_pipeline:
        mock_generator = Mock()
        mock_generator.side_effect = Exception("Test exception")
        patched_pipeline.return_value = mock_generator
        service = HuggingFaceTextCompletion(service_id=model_name, ai_model_id=model_name, task=task)
        kernel.add_service(service=service)

        exec_settings = PromptExecutionSettings(service_id=model_name, extension_data={"max_new_tokens": 25})

        prompt = "{{$input}}"
        prompt_template_config = PromptTemplateConfig(template=prompt, execution_settings=exec_settings)

        kernel.add_function(
            prompt_template_config=prompt_template_config,
            function_name="TestFunction",
            plugin_name="TestPlugin",
            prompt_execution_settings=exec_settings,
        )

        arguments = KernelArguments(input=input_str)

        with pytest.raises(
            KernelInvokeException, match="Error occurred while invoking function: 'TestPlugin-TestFunction'"
        ):
            await kernel.invoke(function_name="TestFunction", plugin_name="TestPlugin", arguments=arguments)


@pytest.mark.parametrize(
    ("model_name", "task", "input_str"),
    [
        (
            "patrickvonplaten/t5-tiny-random",
            "text2text-generation",
            "translate English to Dutch: Hello, how are you?",
        ),
        ("HuggingFaceM4/tiny-random-LlamaForCausalLM", "text-generation", "Hello, I like sleeping and "),
    ],
    ids=["text2text-generation", "text-generation"],
)
async def test_text_completion_streaming(model_name, task, input_str):
    ret = {"summary_text": "test"} if task == "summarization" else {"generated_text": "test"}
    mock_pipeline = Mock(return_value=ret)

    mock_streamer = MagicMock(spec=TextIteratorStreamer)
    mock_streamer.__iter__.return_value = iter(["mocked_text"])

    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline",
            return_value=mock_pipeline,
        ),
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.Thread",
            side_effect=Mock(spec=Thread),
        ),
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoTokenizer",
            side_effect=Mock(spec=AutoTokenizer),
        ),
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.TextIteratorStreamer",
            return_value=mock_streamer,
        ) as mock_stream,
    ):
        mock_stream.return_value = mock_streamer
        service = HuggingFaceTextCompletion(service_id=model_name, ai_model_id=model_name, task=task)
        prompt = "test prompt"
        exec_settings = PromptExecutionSettings(service_id=model_name, extension_data={"max_new_tokens": 25})

        result = []
        async for content in service.get_streaming_text_contents(prompt, exec_settings):
            result.append(content)

        assert len(result) == 1
        assert result[0][0].inner_content == "mocked_text"


@pytest.mark.parametrize(
    ("model_name", "task", "input_str"),
    [
        (
            "patrickvonplaten/t5-tiny-random",
            "text2text-generation",
            "translate English to Dutch: Hello, how are you?",
        ),
        ("HuggingFaceM4/tiny-random-LlamaForCausalLM", "text-generation", "Hello, I like sleeping and "),
    ],
    ids=["text2text-generation", "text-generation"],
)
async def test_text_completion_streaming_throws(model_name, task, input_str):
    ret = {"summary_text": "test"} if task == "summarization" else {"generated_text": "test"}
    mock_pipeline = Mock(return_value=ret)

    mock_streamer = MagicMock(spec=TextIteratorStreamer)
    mock_streamer.__iter__.return_value = Exception()

    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline",
            return_value=mock_pipeline,
        ),
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.Thread",
            side_effect=Exception(),
        ),
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.TextIteratorStreamer",
            return_value=mock_streamer,
        ) as mock_stream,
    ):
        mock_stream.return_value = mock_streamer
        service = HuggingFaceTextCompletion(service_id=model_name, ai_model_id=model_name, task=task)
        prompt = "test prompt"
        exec_settings = PromptExecutionSettings(service_id=model_name, extension_data={"max_new_tokens": 25})

        with pytest.raises(ServiceResponseException, match=("Hugging Face completion failed")):
            async for _ in service.get_streaming_text_contents(prompt, exec_settings):
                pass


def test_hugging_face_text_completion_init():
    with (
        patch("semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline") as patched_pipeline,
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.torch.cuda.is_available"
        ) as mock_torch_cuda_is_available,
    ):
        patched_pipeline.return_value = patched_pipeline
        mock_torch_cuda_is_available.return_value = False

        ai_model_id = "test-model"
        task = "summarization"
        device = -1

        service = HuggingFaceTextCompletion(service_id="test", ai_model_id=ai_model_id, task=task, device=device)

        assert service is not None
