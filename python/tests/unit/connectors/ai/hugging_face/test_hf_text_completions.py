# Copyright (c) Microsoft. All rights reserved.

import logging
from threading import Thread
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
import torch
from transformers import AutoTokenizer, TextIteratorStreamer

from semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion import (
    HuggingFaceTextCompletion,
    _create_seq2seq_generator,
    _Seq2SeqGenerator,
)
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
            "Falconsai/text_summarization",
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
    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline",
            return_value=mock_pipeline,
        ),
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion._create_seq2seq_generator",
            return_value=mock_pipeline,
        ),
    ):
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
    mock_generator = Mock(side_effect=Exception("Test exception"))

    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion._create_seq2seq_generator",
            return_value=mock_generator,
        ),
    ):
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
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion._create_seq2seq_generator",
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
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion._create_seq2seq_generator",
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


@pytest.mark.parametrize(
    ("task", "output_key", "expected_prefix"),
    [
        ("summarization", "summary_text", "summarize: "),
        ("text2text-generation", "generated_text", ""),
    ],
)
async def test_hugging_face_text_completion_init(task, output_key, expected_prefix):
    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoModelForSeq2SeqLM"
        ) as mock_model_class,
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoTokenizer"
        ) as mock_tokenizer_class,
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.torch.cuda.is_available"
        ) as mock_torch_cuda_is_available,
    ):
        mock_torch_cuda_is_available.return_value = False
        mock_model_class.from_pretrained.return_value.hf_device_map = None
        mock_model_class.from_pretrained.return_value.config.task_specific_params = {
            "summarization": {"prefix": "summarize: "}
        }
        mock_model_class.from_pretrained.return_value.generate.return_value = ["output_ids"]
        mock_tokenizer = mock_tokenizer_class.from_pretrained.return_value
        mock_tokenizer.return_value = {"input_ids": Mock()}
        mock_tokenizer.decode.return_value = "generated text"

        ai_model_id = "test-model"
        device = -1

        service = HuggingFaceTextCompletion(service_id="test", ai_model_id=ai_model_id, task=task, device=device)
        assert service is not None
        mock_model_class.from_pretrained.assert_called_once_with(ai_model_id)
        mock_tokenizer_class.from_pretrained.assert_called_once_with(ai_model_id)
        mock_model_class.from_pretrained.return_value.to.assert_called_once()
        assert service.generator.output_key == output_key
        assert service.generator.prefix == expected_prefix
        result = await service.get_text_contents("input text", PromptExecutionSettings())
        assert [item.text for item in result] == ["generated text"]
        # The task specific prefix must be prepended before tokenization, as the removed pipelines did.
        assert mock_tokenizer.call_args.args[0] == f"{expected_prefix}input text"


async def test_hugging_face_text_completion_forwards_model_kwargs_to_tokenizer():
    """Hub options in model_kwargs must reach the tokenizer, as pipeline() used to do."""
    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoModelForSeq2SeqLM"
        ) as mock_model_class,
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoTokenizer"
        ) as mock_tokenizer_class,
    ):
        mock_model_class.from_pretrained.return_value.hf_device_map = None
        mock_model_class.from_pretrained.return_value.config.task_specific_params = None

        HuggingFaceTextCompletion(
            service_id="test",
            ai_model_id="test-model",
            task="text2text-generation",
            model_kwargs={"token": "secret", "revision": "abc123", "dtype": "float16"},
        )

        mock_model_class.from_pretrained.assert_called_once_with(
            "test-model", token="secret", revision="abc123", dtype="float16"
        )
        mock_tokenizer_class.from_pretrained.assert_called_once_with("test-model", token="secret", revision="abc123")


def test_hugging_face_text_completion_non_seq2seq_task_uses_pipeline():
    """Tasks other than the removed seq2seq ones must still go through `pipeline()`."""
    with (
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.pipeline"
        ) as mock_pipeline_factory,
        patch(
            "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion._create_seq2seq_generator"
        ) as mock_seq2seq_factory,
    ):
        service = HuggingFaceTextCompletion(
            ai_model_id="test-model",
            task="text-generation",
            device=-1,
            model_kwargs={"dtype": "float16"},
            pipeline_kwargs={"trust_remote_code": True},
        )

        mock_seq2seq_factory.assert_not_called()
        mock_pipeline_factory.assert_called_once_with(
            task="text-generation",
            model="test-model",
            device=-1,
            model_kwargs={"dtype": "float16"},
            trust_remote_code=True,
        )
        assert service.generator is mock_pipeline_factory.return_value
        # The service id falls back to the model id.
        assert service.service_id == "test-model"


# region _Seq2SeqGenerator


def _make_tensor(name: str) -> Mock:
    """Build a stand-in tensor that records the device it was moved to."""
    tensor = Mock(name=name)
    tensor.to.return_value = f"{name}@device"
    return tensor


def _make_generator(
    *,
    output_ids: list[str] | None = None,
    decoded: list[str] | None = None,
    encoded: dict[str, Any] | None = None,
    output_key: str = "generated_text",
    prefix: str = "",
    default_call_kwargs: dict[str, Any] | None = None,
) -> tuple[_Seq2SeqGenerator, Mock, Mock]:
    model = Mock()
    model.generate.return_value = output_ids if output_ids is not None else ["ids_0"]
    tokenizer = Mock()
    tokenizer.return_value = dict(encoded if encoded is not None else {"input_ids": _make_tensor("input_ids")})
    tokenizer.decode.side_effect = decoded if decoded is not None else ["decoded_0"]
    generator = _Seq2SeqGenerator(
        model=model,
        tokenizer=tokenizer,
        device=torch.device("cpu"),
        output_key=output_key,
        prefix=prefix,
        default_call_kwargs=default_call_kwargs if default_call_kwargs is not None else {},
    )
    return generator, model, tokenizer


def test_seq2seq_generator_returns_one_record_per_sequence():
    """`num_return_sequences > 1` must yield one record per generated sequence, like the removed pipeline."""
    generator, _, _ = _make_generator(
        output_ids=["ids_0", "ids_1", "ids_2"],
        decoded=["first", "second", "third"],
        output_key="summary_text",
    )

    assert generator("prompt", num_return_sequences=3) == [
        {"summary_text": "first"},
        {"summary_text": "second"},
        {"summary_text": "third"},
    ]


def test_seq2seq_generator_drops_token_type_ids_and_moves_inputs_to_device():
    """`token_type_ids` is not a valid `generate()` argument, and inputs must land on the model device."""
    generator, model, _ = _make_generator(
        encoded={
            "input_ids": _make_tensor("input_ids"),
            "attention_mask": _make_tensor("attention_mask"),
            "token_type_ids": _make_tensor("token_type_ids"),
        },
    )

    generator("prompt")

    model.generate.assert_called_once_with(input_ids="input_ids@device", attention_mask="attention_mask@device")


def test_seq2seq_generator_routes_tokenizer_only_options_away_from_generate():
    """`truncation`/`clean_up_tokenization_spaces` belong to the tokenizer, not to `generate()`."""
    generator, model, tokenizer = _make_generator(
        default_call_kwargs={"truncation": True, "clean_up_tokenization_spaces": True},
    )

    generator("prompt", do_sample=False)

    assert tokenizer.call_args.kwargs["truncation"] is True
    assert tokenizer.decode.call_args.kwargs == {
        "skip_special_tokens": True,
        "clean_up_tokenization_spaces": True,
    }
    model.generate.assert_called_once_with(input_ids="input_ids@device", do_sample=False)


def test_seq2seq_generator_call_kwargs_override_defaults():
    """Per-call settings must win over the defaults captured at construction time."""
    generator, model, _ = _make_generator(default_call_kwargs={"do_sample": True, "num_beams": 4})

    generator("prompt", do_sample=False)

    assert model.generate.call_args.kwargs["do_sample"] is False
    assert model.generate.call_args.kwargs["num_beams"] == 4


# region _create_seq2seq_generator


def _patch_auto_classes(hf_device_map=None, task_specific_params=None, model_device=None):
    """Patch the auto classes used by `_create_seq2seq_generator` and pre-wire the model mock."""
    model_patch = patch("semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoModelForSeq2SeqLM")
    tokenizer_patch = patch("semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.AutoTokenizer")
    mock_model_class = model_patch.start()
    mock_tokenizer_class = tokenizer_patch.start()
    model = mock_model_class.from_pretrained.return_value
    model.hf_device_map = hf_device_map
    model.config.task_specific_params = task_specific_params
    if model_device is not None:
        model.device = model_device
    return mock_model_class, mock_tokenizer_class, [model_patch, tokenizer_patch]


@pytest.fixture
def auto_classes():
    """Yield a factory for patched AutoModelForSeq2SeqLM/AutoTokenizer pairs, cleaning up afterwards."""
    started: list[Any] = []

    def _factory(**kwargs):
        mock_model_class, mock_tokenizer_class, patches = _patch_auto_classes(**kwargs)
        started.extend(patches)
        return mock_model_class, mock_tokenizer_class

    yield _factory
    for active in started:
        active.stop()


def test_create_seq2seq_generator_routes_hub_options_to_model_and_tokenizer(auto_classes):
    """Hub options passed via pipeline_kwargs must reach both loads, as `pipeline()` did."""
    mock_model_class, mock_tokenizer_class = auto_classes()

    _create_seq2seq_generator(
        "test-model",
        "text2text-generation",
        -1,
        None,
        {
            "cache_dir": "/cache",
            "force_download": True,
            "local_files_only": True,
            "revision": "rev",
            "token": "secret",
            "trust_remote_code": True,
        },
    )

    expected = {
        "cache_dir": "/cache",
        "force_download": True,
        "local_files_only": True,
        "revision": "rev",
        "token": "secret",
        "trust_remote_code": True,
    }
    mock_model_class.from_pretrained.assert_called_once_with("test-model", **expected)
    mock_tokenizer_class.from_pretrained.assert_called_once_with("test-model", **expected)


def test_create_seq2seq_generator_splits_model_only_and_tokenizer_only_options(auto_classes):
    """`use_fast` is tokenizer only, `config`/`device_map` are model only, `torch_dtype` maps to `dtype`."""
    mock_model_class, mock_tokenizer_class = auto_classes(hf_device_map={"": 0})
    config = object()

    _create_seq2seq_generator(
        "test-model",
        "text2text-generation",
        -1,
        None,
        {"use_fast": False, "config": config, "device_map": "auto", "torch_dtype": "float16"},
    )

    mock_model_class.from_pretrained.assert_called_once_with(
        "test-model", dtype="float16", config=config, device_map="auto"
    )
    mock_tokenizer_class.from_pretrained.assert_called_once_with("test-model", use_fast=False)


def test_create_seq2seq_generator_model_kwargs_take_precedence(auto_classes):
    """When the same option appears in both dictionaries, `model_kwargs` wins for the model load."""
    mock_model_class, _ = auto_classes()

    _create_seq2seq_generator(
        "test-model",
        "text2text-generation",
        -1,
        {"revision": "from-model-kwargs"},
        {"revision": "from-pipeline-kwargs"},
    )

    mock_model_class.from_pretrained.assert_called_once_with("test-model", revision="from-model-kwargs")


def test_create_seq2seq_generator_warns_and_drops_pipeline_only_options(auto_classes, caplog):
    """Pipeline-only options must be dropped with a warning instead of crashing `generate()`."""
    auto_classes()

    with caplog.at_level(logging.WARNING):
        generator = _create_seq2seq_generator(
            "test-model",
            "text2text-generation",
            -1,
            None,
            {"batch_size": 4, "num_workers": 2, "framework": "pt", "num_beams": 3},
        )

    assert "batch_size" in caplog.text
    assert "framework" in caplog.text
    assert "num_workers" in caplog.text
    # Genuine generation options survive and become defaults for every call.
    assert generator.default_call_kwargs == {"num_beams": 3}


def test_create_seq2seq_generator_accepts_custom_tokenizer_id(auto_classes):
    """A tokenizer repo id different from the model id must be honoured."""
    _, mock_tokenizer_class = auto_classes()

    _create_seq2seq_generator("test-model", "text2text-generation", -1, None, {"tokenizer": "other-tokenizer"})

    mock_tokenizer_class.from_pretrained.assert_called_once_with("other-tokenizer")


def test_create_seq2seq_generator_accepts_preloaded_tokenizer_instance(auto_classes):
    """An already instantiated tokenizer must be used as-is, without a hub round trip."""
    _, mock_tokenizer_class = auto_classes()
    preloaded = Mock()

    generator = _create_seq2seq_generator("test-model", "text2text-generation", -1, None, {"tokenizer": preloaded})

    mock_tokenizer_class.from_pretrained.assert_not_called()
    assert generator.tokenizer is preloaded


def test_create_seq2seq_generator_skips_manual_placement_for_device_map(auto_classes):
    """Accelerate dispatched models are already placed, so `.to()` must not be called."""
    mock_model_class, _ = auto_classes(hf_device_map={"": 0}, model_device=torch.device("cuda:1"))
    model = mock_model_class.from_pretrained.return_value

    generator = _create_seq2seq_generator("test-model", "text2text-generation", -1, {"device_map": "auto"}, None)

    model.to.assert_not_called()
    assert generator.device == torch.device("cuda:1")


def test_create_seq2seq_generator_places_model_on_requested_gpu(auto_classes):
    """A non negative device index must resolve to the matching CUDA device."""
    mock_model_class, _ = auto_classes()
    model = mock_model_class.from_pretrained.return_value

    with patch(
        "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.torch.cuda.is_available",
        return_value=True,
    ):
        _create_seq2seq_generator("test-model", "text2text-generation", 1, None, None)

    model.to.assert_called_once_with(torch.device("cuda:1"))


def test_create_seq2seq_generator_falls_back_to_cpu_without_cuda(auto_classes):
    """Without CUDA the model stays on the CPU even when a GPU index was requested."""
    mock_model_class, _ = auto_classes()
    model = mock_model_class.from_pretrained.return_value

    with patch(
        "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion.torch.cuda.is_available",
        return_value=False,
    ):
        _create_seq2seq_generator("test-model", "text2text-generation", 0, None, None)

    model.to.assert_called_once_with(torch.device("cpu"))


@pytest.mark.parametrize(
    ("task", "task_specific_params", "expected_prefix"),
    [
        ("summarization", {"summarization": {"prefix": "summarize: "}}, "summarize: "),
        ("text2text-generation", {"summarization": {"prefix": "summarize: "}}, ""),
        ("summarization", {"summarization": {"num_beams": 4}}, ""),
        ("summarization", None, ""),
        ("summarization", {}, ""),
    ],
    ids=["matching-task", "other-task", "no-prefix-key", "no-params", "empty-params"],
)
def test_create_seq2seq_generator_resolves_task_prefix(auto_classes, task, task_specific_params, expected_prefix):
    """The prefix is only applied when the model declares one for the requested task."""
    auto_classes(task_specific_params=task_specific_params)

    generator = _create_seq2seq_generator("test-model", task, -1, None, None)

    assert generator.prefix == expected_prefix


# region text content mapping


@pytest.mark.parametrize(
    ("task", "key"),
    [("summarization", "summary_text"), ("text2text-generation", "generated_text")],
)
def test_create_text_content_reads_the_task_specific_key(task, key):
    """`_create_text_content` must read the same key the generator writes."""
    with patch(
        "semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion._create_seq2seq_generator"
    ) as mock_factory:
        mock_factory.return_value.output_key = key
        service = HuggingFaceTextCompletion(ai_model_id="test-model", task=task)

    response = [{key: "the text"}]
    content = service._create_text_content(response, response[0])

    assert content.text == "the text"
    assert content.ai_model_id == "test-model"
    assert content.inner_content is response
    # The generator and the content mapping must agree on the key.
    assert service.generator.output_key == key
