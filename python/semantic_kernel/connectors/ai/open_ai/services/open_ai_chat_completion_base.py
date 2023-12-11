# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
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
        is_submit_tool_outputs: bool = False,
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
                messages=messages, 
                functions=functions
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
        functions: Optional[List[Dict[str, Any]]] = None,
        is_submit_tool_outputs: bool = False,
    ) -> Union[
        Tuple[Optional[str], Optional[FunctionCall]],
        List[Tuple[Optional[str], Optional[FunctionCall]]],
    ]:
        """
        Handle an assistant chat request.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            functions {List[Dict[str, Any]]} -- The functions to use for the chat completion.

        Returns:
            Union[
                Tuple[Optional[str], Optional[FunctionCall]], 
                List[Tuple[Optional[str], Optional[FunctionCall]]]
            ] -- The completion result(s).
        """
        if not self.assistant_id:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "Please first create an assistant.",
            )

        if not self.thread_id:
            thread = await self.client.beta.threads.create(timeout=10)
            self.thread_id = thread.id

        await self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role=messages[-1]["role"],
            content=messages[-1]["content"],
        )

        tools = []
        if functions is not None:
            tools = self._transform_function_definitions(functions)

        run = await self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            tools=tools,
        )

        run = await self._poll_on_run(run)

        if (
            run.status == "requires_action"
            and run.required_action.type == "submit_tool_outputs"
        ):
            tool_calls = run.required_action.submit_tool_outputs.tool_calls

            # Initialize an empty list to store extracted data
            completion = None
            func_calls = None

            # Iterate through each tool_call
            for tool_call in tool_calls:
                # Extract 'name' and 'arguments'
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"Tool Call: {tool_call.id}")
                print(f"Function Name: {name}")
                print(f"Function Arguments:\n{arguments}")

                try:
                    fc = FunctionCall(tool_call_id=str(tool_call.id), name=str(name), arguments=str(arguments))
                except Exception as e:
                    print(f"Exception: {e}")

                func_calls = fc

                break

            # return a list of Tuple[Optional[str], Optional[FunctionCall]]
            return completion, func_calls

            # need to run the function here, how do we do that?
            # await self.client.beta.threads.runs.submit_tool_outputs(
            #     run_id=run.id,
            #     thread_id=self.thread_id,
            #     tool_outputs=run.required_action.tool_outputs,
            # )

        run = await self._poll_on_run(run)

        response = await self.client.beta.threads.messages.list(
            thread_id=self.thread_id, order="desc"
        )
        if hasattr(response, "data"):
            # Filtering to get only assistant messages
            assistant_messages = [
                message for message in response.data if message.role == "assistant"
            ]

            # Do we need to concatenate all assistant messages?
            if assistant_messages:
                assistant_response = assistant_messages[0]
                if assistant_response.content:
                    return (assistant_response.content[0].text.value, None)
            else:
                return []
        else:
            return []

    async def _poll_on_run(self, run: Run) -> Run:
        while run.status in ["queued", "in_progress"]:
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id, run_id=run.id
            )
            await asyncio.sleep(0.5)
        return run

    def _transform_function_definitions(self, functions):
        transformed_functions = []

        for func in functions:
            transformed_function = {"type": "function", "function": func}
            transformed_functions.append(transformed_function)

        return transformed_functions

    @staticmethod
    def _parse_choices(choice) -> Tuple[str, int]:
        message = ""
        if choice.delta.content:
            message += choice.delta.content

        return message, choice.index
