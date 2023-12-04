# Copyright (c) Microsoft. All rights reserved.


from dataclasses import asdict
from logging import Logger
from typing import Any, AsyncGenerator, Dict, List, Optional, Union, Tuple

from openai.lib.azure import AsyncAzureADTokenProvider
from openai import AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.const import (
    DEFAULT_AZURE_WITH_DATA_API_VERSION,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.azure_chat_with_data_settings import (
    AzureChatWithDataSettings,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.azure_chat_with_data_response import (
    AzureChatWithDataStreamResponse,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)


from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)
from semantic_kernel.sk_pydantic import HttpsUrl


class AzureChatCompletionWithData(AzureChatCompletion):
    _data_source_settings: AzureChatWithDataSettings

    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[Union[HttpsUrl, str]] = None,
        api_key: Optional[str] = None,
        api_version: str = DEFAULT_AZURE_WITH_DATA_API_VERSION,
        data_source_settings: Optional[AzureChatWithDataSettings] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an AzureChatCompletionWithData service.

        You must provide:
        - A deployment_name, endpoint, api_key, and datasource_settings (plus, optionally: ad_token or ad_token_provider)

        :param deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        :param endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal.
        :param api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        :param api_version: The API version to use. (Optional)
            The default value is "2022-12-01".
        :param data_source_settings: The settings for the data source.
        :param log: The logger instance to use. (Optional)
        :param ad_token: The Azure AD token to use. (Optional)
        :param ad_token_provider: The Azure AD token provider to use. (Optional)
        """
        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")

        base_url = f"{str(endpoint).rstrip('/')}/openai/deployments/{deployment_name}/extensions"

        if isinstance(endpoint, str):
            endpoint = HttpsUrl(endpoint)
        if not data_source_settings:
            raise ValueError("The data source settings cannot be `None`")

        super().__init__(
            deployment_name,
            endpoint=endpoint,
            base_url=base_url,
            api_version=api_version,
            api_key=api_key,
            log=log,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
        )

        self._data_source_settings = data_source_settings

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[Tuple[str, str], List[Tuple[str, str]]]:
        """Executes a chat completion request with data and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[Tuple[str, str], List[Tuple[str,str]]] -- The completion result(s) in the format (assistant_message, tool_message).
            The tool message contains additional information about the data source including citations.
        """
        response = await self._send_request(
            messages=messages, request_settings=settings, stream=False
        )

        if len(response.choices) == 1:
            return self._parse_message(response.choices[0].message)
        else:
            return [self._parse_message(choice.message) for choice in response.choices]

    def _parse_message(
        self, message: ChatCompletionMessage, functions: bool = False
    ) -> Tuple[str, str]:
        """Parses the message from the response, returns a tuple of (assistant response, tool response)."""
        assistant_content = message.content
        tool_content = ""
        if message.model_extra and "context" in message.model_extra:
            for m in message.model_extra["context"].get("messages", []):
                if m["role"] == "tool":
                    tool_content = m.get("content", "")
                    break

        if functions:
            function_call = (
                message.function_call if hasattr(message, "function_call") else None
            )
            if function_call:
                function_call = FunctionCall(
                    name=function_call.name,
                    arguments=function_call.arguments,
                )
            return (assistant_content, tool_content, function_call)

        return (assistant_content, tool_content)

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        response = await self._send_request(
            messages=messages, request_settings=settings, stream=True
        )

        return AzureChatWithDataStreamResponse(response, settings)

    @staticmethod
    def _parse_choices(choice) -> Tuple[str, int]:
        message = ""
        if choice.delta.content:
            message += choice.delta.content

        return message, choice.index

    async def _send_request(
        self,
        request_settings: Union[CompleteRequestSettings, ChatRequestSettings],
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[ChatCompletion, AsyncStream[ChatCompletionChunk],]:
        """
        Completes the given prompt. Returns a single string completion.
        Cannot return multiple completions. Cannot return logprobs.

        Arguments:
            prompt {str} -- The prompt to complete.
            messages {List[Tuple[str, str]]} -- A list of tuples, where each tuple is a role and content set.
            request_settings {CompleteRequestSettings} -- The request settings.
            stream {bool} -- Whether to stream the response.

        Returns:
            ChatCompletion, Completion, AsyncStream[Completion | ChatCompletionChunk] -- The completion response.
        """
        chat_mode = self.ai_model_type == OpenAIModelTypes.CHAT
        self._validate_request(request_settings, prompt, messages, chat_mode)
        model_args = self._create_model_args(
            request_settings, stream, prompt, messages, functions, chat_mode
        )
        try:
            response = await (
                self.client.chat.completions.create(**model_args)
                if chat_mode
                else self.client.completions.create(**model_args)
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex
        if not isinstance(response, AsyncStream):
            if response.usage:
                self.log.info(f"OpenAI usage: {response.usage}")
                self.prompt_tokens += response.usage.prompt_tokens
                self.completion_tokens += response.usage.completion_tokens
                self.total_tokens += response.usage.total_tokens
        return response

    def _create_model_args(
        self, request_settings, stream, prompt, messages, functions, chat_mode
    ):
        model_args = self.get_model_args()
        model_args.update(
            {
                "stream": stream,
                "temperature": request_settings.temperature,
                "top_p": request_settings.top_p,
                "stop": (
                    request_settings.stop_sequences
                    if request_settings.stop_sequences is not None
                    and len(request_settings.stop_sequences) > 0
                    else None
                ),
                "max_tokens": request_settings.max_tokens,
                "extra_body": {
                    "dataSources": [
                        {
                            "type": self._data_source_settings.data_source_type.value,
                            "parameters": asdict(
                                self._data_source_settings.data_source_parameters
                            ),
                        }
                    ]
                }
                ## Following parameters are not yet supported with data.
                # "presence_penalty": request_settings.presence_penalty,
                # "frequency_penalty": request_settings.frequency_penalty,
                # "logit_bias": (
                #     request_settings.token_selection_biases
                #     if request_settings.token_selection_biases is not None
                #     and len(request_settings.token_selection_biases) > 0
                #     else {}
                # ),
                # "n": request_settings.number_of_responses,
            }
        )
        if not chat_mode:
            model_args["prompt"] = prompt
            if hasattr(request_settings, "logprobs"):
                model_args["logprobs"] = request_settings.logprobs
            return model_args

        model_args["messages"] = messages or [{"role": "user", "content": prompt}]
        if functions and request_settings.function_call is not None:
            model_args["function_call"] = request_settings.function_call
            if request_settings.function_call != "auto":
                model_args["functions"] = [
                    func
                    for func in functions
                    if func["name"] == request_settings.function_call
                ]
            else:
                model_args["functions"] = functions

        if hasattr(request_settings, "inputLanguage"):
            model_args["extra_body"]["inputLanguage"] = request_settings.inputLanguage
        if hasattr(request_settings, "outputLanguage"):
            model_args["extra_body"]["outputLanguage"] = request_settings.outputLanguage

        return model_args

    async def complete_chat_with_functions_async(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        request_settings: ChatRequestSettings,
        logger: Logger = None,
    ):
        response = await self._send_request(
            messages=messages,
            request_settings=request_settings,
            stream=False,
            functions=functions,
        )

        if len(response.choices) == 1:
            return self._parse_message(response.choices[0].message, True)
        else:
            return [
                self._parse_message(choice.message, True) for choice in response.choices
            ]

    async def complete_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Logger = None,
    ):
        raise AIException(
            AIException.ErrorCodes.InvalidRequest,
            "AzureChatCompletionWithData does not support completions. Use complete_chat_async instead.",
        )

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Logger = None,
    ):
        raise AIException(
            AIException.ErrorCodes.InvalidRequest,
            "AzureChatCompletionWithData does not support completions. Use complete_chat_stream_async instead.",
        )
