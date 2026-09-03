# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from threading import Thread
from typing import Any, ClassVar, Literal

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, TextIteratorStreamer, pipeline

from semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings import HuggingFacePromptExecutionSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError, ServiceResponseException
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_streaming_text_completion,
    trace_text_completion,
)

logger: logging.Logger = logging.getLogger(__name__)


class _Seq2SeqGenerator:
    """Compatibility adapter for sequence-to-sequence pipelines removed in Transformers 5."""

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        device: torch.device,
        output_key: str,
        prefix: str,
        default_call_kwargs: dict[str, Any],
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.output_key = output_key
        self.prefix = prefix
        self.default_call_kwargs = default_call_kwargs

    def __call__(self, inputs: str, **kwargs: Any) -> list[dict[str, str]]:
        call_kwargs = {**self.default_call_kwargs, **kwargs}
        truncation = call_kwargs.pop("truncation", False)
        clean_up_tokenization_spaces = call_kwargs.pop("clean_up_tokenization_spaces", False)
        model_inputs = self.tokenizer(self.prefix + inputs, truncation=truncation, return_tensors="pt")
        model_inputs.pop("token_type_ids", None)
        model_inputs = {name: value.to(self.device) for name, value in model_inputs.items()}
        output_ids = self.model.generate(**model_inputs, **call_kwargs)
        return [
            {
                self.output_key: self.tokenizer.decode(
                    result,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                )
            }
            for result in output_ids
        ]


def _create_seq2seq_generator(
    ai_model_id: str,
    task: str,
    device: int,
    model_kwargs: dict[str, Any] | None,
    pipeline_kwargs: dict[str, Any] | None,
) -> _Seq2SeqGenerator:
    pipeline_options = dict(pipeline_kwargs or {})
    model_load_kwargs = dict(model_kwargs or {})
    # `pipeline()` used to share `model_kwargs` with the tokenizer, minus the model-only entries.
    tokenizer_load_kwargs = {
        name: value
        for name, value in model_load_kwargs.items()
        if name not in ("config", "device_map", "dtype", "quantization_config", "torch_dtype")
    }
    for option in ("cache_dir", "force_download", "local_files_only", "revision", "token", "trust_remote_code"):
        if option in pipeline_options:
            value = pipeline_options.pop(option)
            model_load_kwargs.setdefault(option, value)
            tokenizer_load_kwargs[option] = value
    if "use_fast" in pipeline_options:
        tokenizer_load_kwargs["use_fast"] = pipeline_options.pop("use_fast")
    if "torch_dtype" in pipeline_options:
        model_load_kwargs.setdefault("dtype", pipeline_options.pop("torch_dtype"))
    for option in ("config", "device_map", "dtype"):
        if option in pipeline_options:
            model_load_kwargs.setdefault(option, pipeline_options.pop(option))
    ignored_options = {
        option: pipeline_options.pop(option)
        for option in (
            "batch_size",
            "binary_output",
            "feature_extractor",
            "framework",
            "image_processor",
            "num_workers",
            "pipeline_class",
            "processor",
        )
        if option in pipeline_options
    }
    if ignored_options:
        logger.warning(
            "Ignoring pipeline options that do not apply to sequence-to-sequence generation: %s",
            ", ".join(sorted(ignored_options)),
        )

    model = AutoModelForSeq2SeqLM.from_pretrained(ai_model_id, **model_load_kwargs)
    tokenizer_id = pipeline_options.pop("tokenizer", ai_model_id)
    tokenizer = (
        AutoTokenizer.from_pretrained(tokenizer_id, **tokenizer_load_kwargs)
        if isinstance(tokenizer_id, str)
        else tokenizer_id
    )
    resolved_device = torch.device(f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu")
    if getattr(model, "hf_device_map", None) is None:
        model.to(resolved_device)
    model_device = getattr(model, "device", resolved_device)
    output_key = "summary_text" if task == "summarization" else "generated_text"
    # The removed pipelines prepended the model's task-specific prefix (e.g. "summarize: ") to the input.
    task_specific_params = getattr(model.config, "task_specific_params", None) or {}
    prefix = task_specific_params.get(task, {}).get("prefix") or ""
    return _Seq2SeqGenerator(
        model=model,
        tokenizer=tokenizer,
        device=model_device,
        output_key=output_key,
        prefix=prefix,
        default_call_kwargs=pipeline_options,
    )


class HuggingFaceTextCompletion(TextCompletionClientBase):
    """Hugging Face text completion service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "huggingface"

    task: Literal["summarization", "text-generation", "text2text-generation"]
    device: str
    generator: Any

    def __init__(
        self,
        ai_model_id: str,
        task: str | None = "text2text-generation",
        device: int = -1,
        service_id: str | None = None,
        model_kwargs: dict[str, Any] | None = None,
        pipeline_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Initializes a new instance of the HuggingFaceTextCompletion class.

        Args:
            ai_model_id (str): Hugging Face model card string, see
                https://huggingface.co/models
            device (int): Device to run the model on, defaults to CPU, 0+ for GPU,
                -- None if using device_map instead. (If both device and device_map
                are specified, device overrides device_map. If unintended,
                it can lead to unexpected behavior.) (optional)
            service_id (str): Service ID for the AI service. (optional)
            task (str): Model completion task type, options are:
                - summarization: takes a long text and returns a shorter summary.
                - text-generation: takes incomplete text and returns a set of completion candidates.
                - text2text-generation (default): takes an input prompt and returns a completion.
                text2text-generation is the default as it behaves more like GPT-3+. (optional)
            model_kwargs (dict[str, Any]): Additional dictionary of keyword arguments
                passed along to the model's `from_pretrained(..., **model_kwargs)` function. (optional)
            pipeline_kwargs (dict[str, Any]): Additional keyword arguments passed along
                to the specific pipeline init (see the documentation for the corresponding pipeline class
                for possible values). (optional)

        Note that this model will be downloaded from the Hugging Face model hub.
        """
        if task in {"summarization", "text2text-generation"}:
            generator = _create_seq2seq_generator(ai_model_id, task, device, model_kwargs, pipeline_kwargs)
        else:
            generator = pipeline(
                task=task,  # type: ignore[arg-type]
                model=ai_model_id,
                device=device,
                model_kwargs=model_kwargs,
                **pipeline_kwargs or {},
            )
        resolved_device = f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"
        super().__init__(
            service_id=service_id or ai_model_id,
            ai_model_id=ai_model_id,
            task=task,
            device=resolved_device,
            generator=generator,
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return HuggingFacePromptExecutionSettings

    @override
    @trace_text_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        if not isinstance(settings, HuggingFacePromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, HuggingFacePromptExecutionSettings)  # nosec

        try:
            results = self.generator(prompt, **settings.prepare_settings_dict())
        except Exception as e:
            raise ServiceResponseException("Hugging Face completion failed") from e

        if isinstance(results, list):
            return [self._create_text_content(results, result) for result in results]
        return [self._create_text_content(results, results)]

    @override
    @trace_streaming_text_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        if not isinstance(settings, HuggingFacePromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, HuggingFacePromptExecutionSettings)  # nosec

        if settings.num_return_sequences > 1:
            raise ServiceInvalidExecutionSettingsError(
                "HuggingFace TextIteratorStreamer does not stream multiple responses in a parsable format."
                " If you need multiple responses, please use the complete method.",
            )
        try:
            streamer = TextIteratorStreamer(AutoTokenizer.from_pretrained(self.ai_model_id))
            # See https://github.com/huggingface/transformers/blob/main/src/transformers/generation/streamers.py#L159
            thread = Thread(
                target=self.generator, args={prompt}, kwargs=settings.prepare_settings_dict(streamer=streamer)
            )
            thread.start()

            for new_text in streamer:
                yield [
                    StreamingTextContent(
                        choice_index=0, inner_content=new_text, text=new_text, ai_model_id=self.ai_model_id
                    )
                ]

            thread.join()
        except Exception as e:
            raise ServiceResponseException("Hugging Face completion failed") from e

    # endregion

    def _create_text_content(self, response: Any, candidate: dict[str, str]) -> TextContent:
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            text=candidate["summary_text" if self.task == "summarization" else "generated_text"],
        )
