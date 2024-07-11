# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from threading import Thread
from typing import Any, Dict, List, Optional, Union

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class HuggingFaceTextCompletion(TextCompletionClientBase):
    _model_id: str
    _task: str
    _device: int
    _log: Logger

    def __init__(
        self,
        model_id: str,
        device: Optional[int] = -1,
        task: Optional[str] = None,
        log: Optional[Logger] = None,
        model_kwargs: Dict[str, Any] = None,
        pipeline_kwargs: Dict[str, Any] = {},
    ) -> None:
        """
        Initializes a new instance of the HuggingFaceTextCompletion class.

        Arguments:
            model_id {str} -- Hugging Face model card string, see
                https://huggingface.co/models
            device {Optional[int]} -- Device to run the model on, -1 for CPU, 0+ for GPU.
            task {Optional[str]} -- Model completion task type, options are:
                - summarization: takes a long text and returns a shorter summary.
                - text-generation: takes incomplete text and returns a set of completion candidates.
                - text2text-generation (default): takes an input prompt and returns a completion.
                text2text-generation is the default as it behaves more like GPT-3+.
            log {Optional[Logger]} -- Logger instance.
            model_kwargs {Optional[Dict[str, Any]]} -- Additional dictionary of keyword arguments
                passed along to the model's `from_pretrained(..., **model_kwargs)` function.
            pipeline_kwargs {Optional[Dict[str, Any]]} -- Additional keyword arguments passed along
                to the specific pipeline init (see the documentation for the corresponding pipeline class
                for possible values).

        Note that this model will be downloaded from the Hugging Face model hub.
        """
        self._model_id = model_id
        self._task = "text2text-generation" if task is None else task
        self._log = log if log is not None else NullLogger()
        self._model_kwargs = model_kwargs
        self._pipeline_kwargs = pipeline_kwargs

        try:
            import torch
            import transformers
        except (ImportError, ModuleNotFoundError):
            raise ImportError(
                "Please ensure that torch and transformers are installed to use HuggingFaceTextCompletion"
            )

        self.device = (
            "cuda:" + str(device)
            if device >= 0 and torch.cuda.is_available()
            else "cpu"
        )

        self.generator = transformers.pipeline(
            task=self._task,
            model=self._model_id,
            device=self.device,
            model_kwargs=self._model_kwargs,
            **self._pipeline_kwargs
        )

    async def complete_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        try:
            import transformers

            generation_config = transformers.GenerationConfig(
                temperature=request_settings.temperature,
                top_p=request_settings.top_p,
                max_new_tokens=request_settings.max_tokens,
                pad_token_id=50256,  # EOS token
            )

            results = self.generator(
                prompt,
                do_sample=True,
                num_return_sequences=request_settings.number_of_responses,
                generation_config=generation_config,
            )

            completions = list()
            if self._task == "text-generation" or self._task == "text2text-generation":
                for response in results:
                    completions.append(response["generated_text"])
                if len(completions) == 1:
                    return completions[0]
                else:
                    return completions

            elif self._task == "summarization":
                for response in results:
                    completions.append(response["summary_text"])
                if len(completions) == 1:
                    return completions[0]
                else:
                    return completions

            else:
                raise AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    "Unsupported hugging face pipeline task: only \
                        text-generation, text2text-generation, and summarization are supported.",
                )

        except Exception as e:
            raise AIException("Hugging Face completion failed", e)

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        """
        Streams a text completion using a Hugging Face model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {CompleteRequestSettings} -- Request settings.

        Yields:
            str -- Completion result.
        """
        if request_settings.number_of_responses > 1:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "HuggingFace TextIteratorStreamer does not stream multiple responses in a parseable format. \
                    If you need multiple responses, please use the complete_async method.",
            )
        try:
            import transformers

            generation_config = transformers.GenerationConfig(
                temperature=request_settings.temperature,
                top_p=request_settings.top_p,
                max_new_tokens=request_settings.max_tokens,
                pad_token_id=50256,  # EOS token
            )

            tokenizer = transformers.AutoTokenizer.from_pretrained(self._model_id)
            streamer = transformers.TextIteratorStreamer(tokenizer)
            args = {prompt}
            kwargs = {
                "num_return_sequences": request_settings.number_of_responses,
                "generation_config": generation_config,
                "streamer": streamer,
                "do_sample": True,
            }

            # See https://github.com/huggingface/transformers/blob/main/src/transformers/generation/streamers.py#L159
            thread = Thread(target=self.generator, args=args, kwargs=kwargs)
            thread.start()

            for new_text in streamer:
                yield new_text

            thread.join()

        except Exception as e:
            raise AIException("Hugging Face completion failed", e)
