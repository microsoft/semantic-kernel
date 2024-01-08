# Copyright (c) Microsoft. All rights reserved.

import logging
import asyncio
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    overload,
)

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from openai.types.beta.threads.run import Run
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_const import (
    ACTION_STATE,
    REQUIRED_ACTION_TYPE,
    RUN_STATUS_CANCELED,
    RUN_STATUS_FAILED,
    RUN_STATUS_IN_PROGRESS,
    RUN_STATUS_QUEUED,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_tool_output import (
    OpenAIToolOutput,
)
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
    OpenAIRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_assistant_settings import (
    OpenAIAssistantSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.utils import _parse_choices, _parse_message

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SEC = 10

class OpenAIChatCompletion(OpenAIConfigBase, ChatCompletionClientBase, OpenAITextCompletionBase):
    """OpenAI Chat completion class."""

    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        log: Optional[Any] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
            log: The logger instance to use. (Optional) (Deprecated)
            is_assistant: Whether this is an assistant. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
            is_assistant: Whether this is an assistant. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
            is_assistant: Whether this is an assistant. (Optional)
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        log: Optional[Any] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
            is_assistant: Whether this is an assistant. (Optional)
        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            ai_model_type=OpenAIModelTypes.CHAT,
            default_headers=default_headers,
            async_client=async_client,
            is_assistant=is_assistant,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAIChatCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAIChatCompletion(
            ai_model_id=settings["ai_model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            default_headers=settings.get("default_headers"),
        )

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> Union[Tuple[Optional[str], Optional[FunctionCall]], List[Tuple[Optional[str], Optional[FunctionCall]]],]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        if self.is_assistant:
            return await self._handle_assistant_chat_async(messages)
        else:
            settings.messages = messages
            settings.stream = False
            if settings.ai_model_id is None:
                settings.ai_model_id = self.ai_model_id
            response = await self._send_request(request_settings=settings)

            if len(response.choices) == 1:
                return _parse_message(response.choices[0].message)
            else:
                return [_parse_message(choice.message) for choice in response.choices]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        # OpenAI assistants don't allow streaming, so block until that is available
        if self.is_assistant:
            raise AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                "complete_chat_stream_async for assistants is not currently supported.",
            )

        settings.messages = messages
        settings.stream = True
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)

        # parse the completion text(s) and yield them
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                for choice in chunk.choices:
                    text, index = _parse_choices(choice)
                    completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                text, index = _parse_choices(chunk.choices[0])
                yield text

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return OpenAIChatRequestSettings

    # --------------------------------- OpenAI Assistants -------------------------

    def get_assistant_id(self) -> Optional[str]:
        """
        Get the assistant id if this is an assistant and has been initialized.

        Returns:
            Optional[str]: The assistant id or None if this is not an assistant or not initialized.
        """
        if self.is_assistant and self.assistant_id is not None:
            return self.assistant_id
        return None

    async def delete_thread_async(self) -> None:
        """
        Delete the current thread if this is an assistant.

        Returns:
            None
        """
        if (
            self.is_assistant
            and self.assistant_id is not None
            and self.thread_id is not None
        ):
            await self.client.beta.threads.delete(self.thread_id)

    async def delete_assistant_async(self) -> None:
        """
        Delete the current assistant if this is an assistant.

        Returns:
            None
        """
        if self.is_assistant and self.assistant_id is not None:
            await self.client.beta.assistants.delete(self.assistant_id)

    async def create_assistant_async(
            self,
            assistant_settings: OpenAIAssistantSettings,
            overwrite: bool = True,
        ) -> None:
            """
            Create an assistant with the provided name, description, and instructions.

            Args:
                name (str): The name of the assistant
                description (str): The description of the assistant
                instructions (str): The instructions of the assistant

            Returns:
                str: The ID of the created assistant
            """
            if not self.is_assistant:
                raise AIException(
                    AIException.ErrorCodes.FunctionTypeNotSupported,
                    "create_assistant_async is only supported for assistants.",
                )

            if assistant_settings is None:
                raise AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    "Please provide assistant settings.",
                )

            # Only create an assistant if it doesn't exist or if assistant exists and overwrite is True
            if self.assistant_id and not overwrite:
                return

            assistant = await self.client.beta.assistants.create(
                name=assistant_settings.name,
                instructions=assistant_settings.instructions,
                description=assistant_settings.description,
                model=self.ai_model_id,
            )
            self.assistant_id = assistant.id

            return

    async def _handle_assistant_chat_async(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]] = None,
    ) -> Tuple[str, List[FunctionCall]]:
        """
        Handle an assistant chat request.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            functions (List[Dict[str, Any]]): A list of function definitions.

        Returns:
            Tuple[str, List[FunctionCall]]: A tuple containing the assistant's response and a list of function calls.
        """
        await self._validate_assistant_configuration_async()

        if self.is_tool_output_required and self.run is not None:
            await self._handle_tool_output_async(messages)
        else:
            await self._handle_chat_and_functions_async(messages, functions)

        return await self._finalize_response_async()

    async def _validate_assistant_configuration_async(self) -> None:
        """
        Validate the assistant and thread configurations.

        Raises:
            AIException: If the assistant or thread is not configured.

        Returns:
            None
        """
        if not self.assistant_id:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "Please first create an assistant.",
            )
        if not self.thread_id:
            self.thread_id = await self._create_thread_async()

    async def _create_thread_async(self) -> str:
        """
        Create a new thread and return its ID.

        Returns:
            str: The ID of the created thread.
        """
        thread = await self.client.beta.threads.create(timeout=DEFAULT_TIMEOUT_SEC)
        return thread.id

    async def _handle_tool_output_async(
        self,
        messages: List[Dict[str, str]],
    ) -> None:
        """
        Handle the tool output based on the provided messages.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.

        Returns:
            None
        """
        tool_outputs = self._extract_function_data(messages)
        await self._submit_tool_outputs_async(tool_outputs)

    def _extract_function_data(
        self,
        messages: List[Dict[str, str]],
    ) -> List[OpenAIToolOutput]:
        """
        Extracts function-related data from a list of messages.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.

        Returns:
            List[OpenAIToolOutput]: A list of OpenAIToolOutput objects extracted from the messages.
        """
        tool_outputs = []
        for message in reversed(messages):
            if (
                message.get("role") == "function"
                and message.get("tool_call_id") in self.tool_call_ids
            ):
                tool_call_id = message.get("tool_call_id")
                output = message.get("content")
                if tool_call_id and output:
                    tool_output = OpenAIToolOutput(
                        tool_call_id=tool_call_id, output=output
                    )
                    tool_outputs.append(tool_output)

        return tool_outputs

    async def _submit_tool_outputs_async(
        self,
        tool_outputs: List[OpenAIToolOutput],
    ) -> None:
        """
        Submit tool outputs to the thread.

        Args:
            tool_outputs (List[OpenAIToolOutput]): A list of OpenAIToolOutput objects.

        Returns:
            None
        """
        tools_list = [tool.model_dump() for tool in tool_outputs]

        await self.client.beta.threads.runs.submit_tool_outputs(
            run_id=self.run.id, thread_id=self.thread_id, tool_outputs=tools_list
        )
        # The run's state is back to pending, so retrieve it to get the latest status
        self.run = await self.client.beta.threads.runs.retrieve(
            thread_id=self.thread_id, run_id=self.run.id
        )
        await self._poll_on_run_async(self.run)
        self._reset_tool_flags()

    def _reset_tool_flags(self) -> None:
        """
        Reset tool-related flags.

        Returns:
            None
        """
        self.is_tool_output_required = False
        self.tool_call_ids = []

    async def _handle_chat_and_functions_async(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle chat messages and function invocations.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            functions (List[Dict[str, Any]]): A list of function definitions.

        Returns:
            None
        """
        await self._send_latest_message_on_thread_async(messages)
        tools = self._transform_function_definitions(functions) if functions else []
        self.run = await self._create_run_on_thread_and_poll_async(tools)

    def _transform_function_definitions(
        self,
        functions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Transforms function definitions into a specific format.

        Args:
            functions (List[Dict]): A list of function definitions.

        Returns:
            List[Dict]: A list of transformed function definitions.
        """
        transformed_functions = []
        for func in functions:
            transformed_function = {"type": "function", "function": func}
            transformed_functions.append(transformed_function)

        return transformed_functions

    async def _send_latest_message_on_thread_async(self, messages) -> None:
        """
        Send the latest message from the messages list.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.

        Returns:
            None
        """
        # Todo: do we want to send only the latest message?
        # Don't want to duplicate sending old messages if they've
        # already been included in the thread
        await self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role=messages[-1]["role"],
            content=messages[-1]["content"],
        )

    async def _create_run_on_thread_and_poll_async(
        self,
        tools: List[Dict[str, Any]],
    ) -> Run:
        """
        Create a new run with the given tools and poll until completion.

        Args:
            tools (List[Dict]): A list of tool definitions.

        Returns:
            Run: The run object after it exits the queued or in-progress state.
        """
        run = await self.client.beta.threads.runs.create(
            thread_id=self.thread_id, assistant_id=self.assistant_id, tools=tools
        )

        return await self._poll_on_run_async(run)

    async def _poll_on_run_async(self, run: Run) -> Run:
        """
        Polls the status of a run until it is no longer queued or in progress.

        Args:
            run (Run): The run object to be polled.

        Raises:
            AIException: If the run fails.

        Returns:
            Run: The updated run object after it exits the queued or in-progress state.
        """
        while run.status in [RUN_STATUS_QUEUED, RUN_STATUS_IN_PROGRESS]:
            # Retrieve the latest status of the run
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id, run_id=run.id
            )
            await asyncio.sleep(0.5)

        if run.status in [RUN_STATUS_FAILED, RUN_STATUS_CANCELED]:
            raise AIException(
                AIException.ErrorCodes.RunFailed,
                f"Run failed with status: {run.status}",
            )

        return run

    async def _finalize_response_async(self) -> Tuple[List[str], List[FunctionCall]]:
        """
        Finalize the response based on the run status.

        Returns:
            Tuple[List[str], List[FunctionCall]]: A tuple containing the
                assistant's response and a list of function calls.
        """
        if self._is_tool_interaction_required():
            return await self._handle_required_tool_interaction()
        else:
            return await self._get_assistant_response()

    def _is_tool_interaction_required(self) -> bool:
        """
        Check if tool interaction is required.

        Returns:
            bool: True if tool interaction is required, False otherwise.
        """
        return (
            self.run.status == ACTION_STATE
            and self.run.required_action.type == REQUIRED_ACTION_TYPE
        )

    async def _handle_required_tool_interaction(
        self,
    ) -> Tuple[List[str], List[FunctionCall]]:
        """
        Handle the required tool interaction.

        Returns:
            Tuple[str, tool_message, List[FunctionCall]]: A tuple containing the assistant's response and a list of function calls.
        """
        tool_calls = self.run.required_action.submit_tool_outputs.tool_calls
        completions, func_calls = [], []
        self.is_tool_output_required = True

        # Store tool call IDs
        self.tool_call_ids = [str(tool_call.id) for tool_call in tool_calls]

        func_calls = [
            FunctionCall(
                tool_call_id=str(tool_call.id),
                name=str(tool_call.function.name),
                arguments=str(tool_call.function.arguments),
            )
            for tool_call in tool_calls
        ]

        # returns completion, tool_message, function_call
        # Todo: does tool_message need to be the function_call? What is it?
        return completions, None, func_calls

    async def _get_assistant_response(self) -> Tuple[str, List[FunctionCall]]:
        """
        Retrieve the assistant's response.

        Returns:
            Tuple[str, List[FunctionCall]]: A tuple containing the assistant's response and a list of function calls.
        """
        response = await self.client.beta.threads.messages.list(
            thread_id=self.thread_id, order="desc"
        )
        if hasattr(response, "data"):
            assistant_messages = [
                message for message in response.data if message.role == "assistant"
            ]
            if assistant_messages:
                assistant_response = assistant_messages[0]
                if assistant_response.content:
                    return assistant_response.content[0].text.value, None, None
            else:
                return None, None, None
        else:
            return None, None, None
