# Copyright (c) Microsoft. All rights reserved.

import asyncio
from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from openai.types.beta.threads.run import Run

from semantic_kernel.connectors.ai import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_assistant_settings import (
    OpenAIAssistantSettings,
)
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
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.utils import _parse_message

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """
    The OpenAIChatCompletionBase class is the base class for OpenAI chat completion services.
    """

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        """
        Executes a chat completion request and returns the result.
        Currently supports both assistant chat as well as regular chat.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        if self.is_assistant:
            return await self._handle_assistant_chat_async(messages)
        else:
            response = await self._send_request(
                messages=messages, request_settings=settings, stream=False
            )

            if len(response.choices) == 1:
                return response.choices[0].message.content
            else:
                return [choice.message.content for choice in response.choices]

    async def complete_chat_with_functions_async(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        request_settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[
        Tuple[Optional[str], Optional[FunctionCall]],
        List[Tuple[Optional[str], Optional[FunctionCall]]],
    ]:
        """
        Executes a chat completion request and returns the result.
        Currently supports both assistant chat as well as regular chat.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            functions {List[Dict[str, Any]]} -- The functions to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """

        if self.is_assistant:
            return await self._handle_assistant_chat_async(
                messages=messages, functions=functions
            )
        else:
            response = await self._send_request(
                messages=messages,
                request_settings=request_settings,
                stream=False,
                functions=functions,
            )

            if len(response.choices) == 1:
                return _parse_message(response.choices[0].message, self.log)
            else:
                return [
                    _parse_message(choice.message, self.log)
                    for choice in response.choices
                ]

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

        # OpenAI assistants don't allow streaming, so block until that is available
        if self.is_assistant:
            raise AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                "complete_chat_stream_async for assistants is not currently supported.",
            )

        response = await self._send_request(
            messages=messages, request_settings=settings, stream=True
        )

        # parse the completion text(s) and yield them
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                for choice in chunk.choices:
                    text, index = self._parse_choices(choice)
                    completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                text, index = self._parse_choices(chunk.choices[0])
                yield text

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
        thread = await self.client.beta.threads.create(timeout=10)
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
            Tuple[str, List[FunctionCall]]: A tuple containing the assistant's response and a list of function calls.
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

        return completions, func_calls

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
                    return assistant_response.content[0].text.value, None
            else:
                return None, None
        else:
            return None, None

    @staticmethod
    def _parse_choices(choice) -> Tuple[str, int]:
        message = ""
        if choice.delta.content:
            message += choice.delta.content

        return message, choice.index
