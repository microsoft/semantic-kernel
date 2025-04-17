# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable, Sequence
from functools import reduce
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar, cast

from openai import BadRequestError
from openai._streaming import AsyncStream
from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response import Response
from openai.types.responses.response_content_part_added_event import ResponseContentPartAddedEvent
from openai.types.responses.response_created_event import ResponseCreatedEvent
from openai.types.responses.response_error_event import ResponseErrorEvent
from openai.types.responses.response_function_call_arguments_delta_event import ResponseFunctionCallArgumentsDeltaEvent
from openai.types.responses.response_input_text import ResponseInputText
from openai.types.responses.response_item import ResponseItem
from openai.types.responses.response_output_item import ResponseOutputItem
from openai.types.responses.response_output_item_added_event import ResponseOutputItemAddedEvent
from openai.types.responses.response_output_item_done_event import ResponseOutputItemDoneEvent
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent

from semantic_kernel.connectors.ai.function_calling_utils import (
    kernel_function_metadata_to_response_function_call_format,
    merge_function_results,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import ContentFilterAIException
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.status import Status
from semantic_kernel.exceptions.agent_exceptions import (
    AgentExecutionException,
    AgentInvokeException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from openai.types.responses.response_text_config_param import ResponseTextConfigParam
    from openai.types.responses.tool_param import ToolParam

    from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent, ResponsesAgentThread
    from semantic_kernel.contents.function_call_content import FunctionCallContent
    from semantic_kernel.kernel import Kernel

_T = TypeVar("_T", bound="ResponsesAgentThreadActions")

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class ResponsesAgentThreadActions:
    """Responses Agent Thread Actions class."""

    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "incomplete"]

    # region Invocation Methods

    @classmethod
    async def invoke(
        cls: type[_T],
        *,
        agent: "OpenAIResponsesAgent",
        chat_history: "ChatHistory",
        thread: "ResponsesAgentThread",
        store_enabled: bool,
        function_choice_behavior: "FunctionChoiceBehavior",
        arguments: KernelArguments | None = None,
        include: list[
            Literal[
                "file_search_call.results", "message.input_image.image_url", "computer_call_output.output.image_url"
            ]
        ]
        | None = None,
        instructions_override: str | None = None,
        kernel: "Kernel | None" = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[ToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the assistant.

        Args:
            agent: The assistant agent.
            chat_history: The Chat History to use for input.
            thread: The thread to use for the response.
            store_enabled: Whether to store the response.
            arguments: The kernel arguments.
            kernel: The kernel.
            function_choice_behavior: The function choice behavior.
            include: Additional output data to include in the response.
            instructions_override: The instructions override.
            max_output_tokens: The maximum completion tokens.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: The parallel tool calls.
            reasoning: The reasoning effort.
            text: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of tuple of the visibility of the message and the chat message content.
        """
        arguments = KernelArguments() if arguments is None else KernelArguments(**arguments, **kwargs)
        kernel = kernel or agent.kernel

        tools = cls._get_tools(agent=agent, kernel=kernel, function_choice_behavior=function_choice_behavior)  # type: ignore

        base_instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        merged_instructions: str = (
            instructions_override if instructions_override is not None else base_instructions or ""
        )

        # form response options
        response_options = cls._generate_options(
            agent=agent,
            include=include,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            model=model,
            parallel_tool_calls=parallel_tool_calls,
            reasoning=reasoning,
            temperature=temperature,
            text=text,
            top_p=top_p,
            truncation_message_count=truncation,
        )

        response_options = {k: v for k, v in response_options.items() if v is not None}

        override_history = chat_history
        if not store_enabled:
            # Use the thread chat history
            override_history = ChatHistory(messages=[*thread._chat_history.messages, *chat_history.messages])

        previous_response_id = None
        if thread.store_enabled and thread.response_id:
            previous_response_id = thread.response_id

        for request_index in range(function_choice_behavior.maximum_auto_invoke_attempts):
            response = await cls._get_response(
                agent=agent,
                chat_history=override_history,
                merged_instructions=merged_instructions,
                previous_response_id=previous_response_id,
                store_output_enabled=store_enabled,
                tools=tools,
                response_options=response_options,
            )
            if not isinstance(response, Response):
                raise AgentInvokeException("Response is not of type Response")

            if store_enabled:
                thread.response_id = response.id

            if response.status in cls.error_message_states:
                error_message = ""
                if response.error and response.error.message:
                    error_message = response.error.message
                incomplete_details = ""
                if response.incomplete_details:
                    incomplete_details = str(response.incomplete_details.reason)
                raise AgentInvokeException(
                    f"Run failed with status: `{response.status}` for agent `{agent.name}` "
                    f"with error: {error_message} or incomplete details: {incomplete_details}"
                )

            try:
                response = await asyncio.wait_for(
                    cls._poll_until_completed(agent, response),
                    timeout=agent.polling_options.run_polling_timeout.total_seconds(),
                )
            except asyncio.TimeoutError:
                raise AgentInvokeException("Polling timed out before completion.")

            # Check if tool calls are required
            function_calls = cls._get_tool_calls_from_output(response.output)  # type: ignore
            if (fc_count := len(function_calls)) == 0:
                yield True, cls._create_response_message_content(response, agent.ai_model_id, agent.name)  # type: ignore
                break

            response_message = cls._create_response_message_content(response, agent.ai_model_id, agent.name)  # type: ignore
            yield False, response_message
            chat_history.add_message(message=response_message)

            logger.info(f"processing {fc_count} tool calls in parallel.")

            # This function either updates the chat history with the function call results
            # or returns the context, with terminate set to True in which case the loop will
            # break and the function calls are returned.
            results = await asyncio.gather(
                *[
                    kernel.invoke_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        arguments=kwargs.get("arguments"),
                        execution_settings=None,
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_behavior=function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            terminate_flag = any(result.terminate for result in results if result is not None)
            for msg in merge_function_results(chat_history.messages[-len(results) :]):
                # Terminate flag should only be true when the filter's terminate is true
                yield terminate_flag, msg
        else:
            # Do a final call, without function calling when the max has been reached.
            function_choice_behavior = FunctionChoiceBehavior.NoneInvoke()
            response = await cls._get_response(
                agent=agent,
                chat_history=override_history,
                merged_instructions=merged_instructions,
                previous_response_id=previous_response_id,
                store_output_enabled=store_enabled,
                tools=tools,
                response_options=response_options,
            )
            assert isinstance(response, Response)  # nosec
            yield True, cls._create_response_message_content(response, agent.ai_model_id, agent.name)

    @classmethod
    async def invoke_stream(
        cls: type[_T],
        *,
        agent: "OpenAIResponsesAgent",
        chat_history: "ChatHistory",
        thread: "ResponsesAgentThread",
        store_enabled: bool,
        function_choice_behavior: "FunctionChoiceBehavior",
        arguments: KernelArguments | None = None,
        include: list[
            Literal[
                "file_search_call.results", "message.input_image.image_url", "computer_call_output.output.image_url"
            ]
        ]
        | None = None,
        instructions_override: str | None = None,
        kernel: "Kernel | None" = None,
        max_output_tokens: int | None = None,
        output_messages: list["ChatMessageContent"] | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[ToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the assistant.

        Args:
            agent: The assistant agent.
            chat_history: The Chat History to use for input.
            thread: The thread to use for the response.
            store_enabled: Whether to store the response.
            arguments: The kernel arguments.
            kernel: The kernel.
            function_choice_behavior: The function choice behavior.
            include: Additional output data to include in the response.
            instructions_override: The instructions override.
            max_output_tokens: The maximum completion tokens.
            output_messages: The messages to include in the request.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: The parallel tool calls.
            reasoning: The reasoning effort.
            text: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of tuple of the visibility of the message and the chat message content.
        """
        arguments = KernelArguments() if arguments is None else KernelArguments(**arguments, **kwargs)
        kernel = kernel or agent.kernel

        tools = cls._get_tools(agent=agent, kernel=kernel, function_choice_behavior=function_choice_behavior)  # type: ignore

        base_instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        merged_instructions: str = (
            instructions_override if instructions_override is not None else base_instructions or ""
        )

        # form response options
        response_options = cls._generate_options(
            agent=agent,
            include=include,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            model=model,
            parallel_tool_calls=parallel_tool_calls,
            reasoning=reasoning,
            temperature=temperature,
            text=text,
            top_p=top_p,
            truncation_message_count=truncation,
        )

        response_options = {k: v for k, v in response_options.items() if v is not None}

        override_history = chat_history
        if not store_enabled:
            # Use the thread chat history
            override_history = ChatHistory(messages=[*thread._chat_history.messages, *chat_history.messages])

        previous_response_id = None
        if thread.store_enabled and thread.response_id:
            previous_response_id = thread.response_id

        for request_index in range(function_choice_behavior.maximum_auto_invoke_attempts):
            response: AsyncStream[ResponseStreamEvent] = await cls._get_response(  # type: ignore
                agent=agent,
                chat_history=override_history,
                merged_instructions=merged_instructions,
                previous_response_id=previous_response_id,
                store_output_enabled=store_enabled,
                tools=tools,
                response_options=response_options,
                stream=True,
            )

            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False

            async with response as response_stream:
                async for event in response_stream:
                    event = cast(ResponseStreamEvent, event)
                    match event:
                        case ResponseCreatedEvent():
                            logger.debug(f"Agent response created with ID: {event.response.id}")
                            if store_enabled:
                                thread.response_id = event.response.id
                        case ResponseOutputItemAddedEvent():
                            function_calls = cls._get_tool_calls_from_output([event.item])  # type: ignore
                            if function_calls:
                                function_call_returned = True
                            msg = cls._build_streaming_msg(
                                agent=agent,
                                metadata=metadata,
                                event=event,
                                items=function_calls,
                                choice_index=request_index,
                            )
                            all_messages.append(msg)
                        case ResponseFunctionCallArgumentsDeltaEvent():
                            function_call = FunctionCallContent(
                                id=event.item_id,
                                index=getattr(event, "index", None),
                                arguments=event.delta,
                            )
                            msg = cls._build_streaming_msg(
                                agent=agent,
                                metadata=metadata,
                                event=event,
                                items=[function_call],
                                choice_index=request_index,
                            )
                            all_messages.append(msg)
                        case ResponseTextDeltaEvent():
                            text_content = StreamingTextContent(
                                text=event.delta,
                                choice_index=request_index,
                            )
                            msg = cls._build_streaming_msg(
                                agent=agent,
                                metadata=metadata,
                                event=event,
                                items=[text_content],
                                choice_index=request_index,
                            )
                            yield msg
                        case ResponseOutputItemDoneEvent():
                            msg = cls._create_output_item_done(agent, event.item)  # type: ignore
                            if output_messages is not None:
                                output_messages.append(msg)
                        case ResponseErrorEvent():
                            logger.error(
                                f"Error in agent invoke_stream: {event.message} "
                                f"(code: {event.code if event.code else 'unknown'})"
                            )
                            break

            if not function_call_returned:
                return

            full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_messages)
            if output_messages is not None:
                # Append the content with function call content to the msgs used for the callback
                output_messages.append(full_completion)
            function_calls = [item for item in full_completion.items if isinstance(item, FunctionCallContent)]
            chat_history.add_message(message=full_completion)

            fc_count = len(function_calls)
            logger.info(f"processing {fc_count} tool calls in parallel.")

            # This function either updates the chat history with the function call results
            # or returns the context, with terminate set to True in which case the loop will
            # break and the function calls are returned.
            results = await asyncio.gather(
                *[
                    kernel.invoke_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        arguments=kwargs.get("arguments"),
                        is_streaming=True,
                        execution_settings=None,
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_behavior=function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            # Merge and yield the function results, regardless of the termination status
            # Include the ai_model_id so we can later add two streaming messages together
            # Some settings may not have an ai_model_id, so we need to check for it
            function_result_messages = cls._merge_streaming_function_results(
                messages=chat_history.messages[-len(results) :],  # type: ignore
                name=agent.name,
                ai_model_id=agent.ai_model_id,  # type: ignore
                function_invoke_attempt=request_index,
            )
            if cls._yield_function_result_messages(function_result_messages):
                msg = function_result_messages[0]
                if output_messages is not None:
                    output_messages.append(msg)

            if any(result.terminate for result in results if result is not None):
                break  # Only break if any result has terminate=True

    # endregion

    # region Helper Methods

    @classmethod
    async def _get_response(
        cls: type[_T],
        agent: "OpenAIResponsesAgent",
        chat_history: "ChatHistory",
        merged_instructions: str | None = None,
        previous_response_id: str | None = None,
        store_output_enabled: bool | None = None,
        tools: Any | None = None,
        response_options: dict | None = None,
        stream: bool = False,
    ) -> Response | AsyncStream[ResponseStreamEvent]:
        try:
            response: Response = await agent.client.responses.create(
                input=cls._prepare_chat_history_for_request(chat_history),
                instructions=merged_instructions or agent.instructions,
                previous_response_id=previous_response_id,
                store=store_output_enabled,
                tools=tools,  # type: ignore
                stream=stream,
                **response_options,
            )
        except BadRequestError as ex:
            if ex.code == "content_filter":
                raise ContentFilterAIException(
                    f"{type(agent)} encountered a content error",
                    ex,
                ) from ex
            raise AgentExecutionException(
                f"{type(agent)} failed to complete the request",
                ex,
            ) from ex
        except Exception as ex:
            raise AgentExecutionException(
                f"{type(agent)} service failed to complete the request",
                ex,
            ) from ex
        if response is None:
            raise AgentInvokeException("Response is None")
        return response

    @classmethod
    async def _poll_until_completed(cls: type[_T], agent: "OpenAIResponsesAgent", response: Response):
        while response.status != "completed":
            await asyncio.sleep(agent.polling_options.default_polling_interval.total_seconds())
            response = await agent.client.responses.retrieve(response.id)
        return response

    @classmethod
    async def get_messages(
        cls: type[_T],
        client: "AsyncOpenAI",
        response_id: str,
        limit: int | None = None,
        sort_order: Literal["asc", "desc"] | None = None,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Get messages from a thread.

        Args:
            client: The client to use to get the messages.
            response_id: The ID of the response to get the messages from.
            limit: The maximum number of messages to get.
            sort_order: The order to sort the messages in.

        Yields:
            An AsyncIterale of ChatMessageContent that includes the response messages.
        """
        last_id: str | None = None

        while True:
            responses = await client.responses.input_items.list(
                response_id=response_id,
                limit=limit,  # type: ignore
                order=sort_order,  # type: ignore
                after=last_id,  # type: ignore
            )

            if not responses:
                break

            for response in responses.data:
                last_id = response.id

                content = cls._create_response_message_content_for_response_item(response)  # type: ignore

                if len(content.items) > 0:
                    yield content

            if not responses.has_more:
                break

    @classmethod
    def _build_streaming_msg(
        cls: type[_T],
        *,
        agent: "OpenAIResponsesAgent",
        metadata: dict[str, str] | None,
        event: ResponseStreamEvent,
        items: list[Any],
        choice_index: int,
        role: str = "assistant",
    ) -> StreamingChatMessageContent:
        """Helper to create StreamingChatMessageContent."""
        return StreamingChatMessageContent(
            inner_content=event,
            ai_model_id=agent.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role),
            items=items,
            choice_index=choice_index,
            name=agent.name,
        )

    @classmethod
    def _yield_function_result_messages(
        cls: type[_T], function_result_messages: Sequence[ChatMessageContent | StreamingChatMessageContent]
    ) -> bool:
        """Determine if the function result messages should be yielded.

        If there are messages and if the first message has items, then yield the messages.
        """
        return len(function_result_messages) > 0 and len(function_result_messages[0].items) > 0

    @classmethod
    def _merge_streaming_function_results(
        cls: type[_T],
        messages: list["StreamingChatMessageContent"],
        name: str,
        ai_model_id: str | None = None,
        function_invoke_attempt: int | None = None,
    ) -> list["StreamingChatMessageContent"]:
        """Combine multiple streaming function result content types to one streaming chat message content type.

        This method combines the FunctionResultContent items from separate StreamingChatMessageContent messages,
        and is used in the event that the `context.terminate = True` condition is met.

        Args:
            messages: The list of streaming chat message content types.
            name: The name of the agent.
            ai_model_id: The AI model ID.
            function_invoke_attempt: The function invoke attempt.

        Returns:
            The combined streaming chat message content type.
        """
        items: list[Any] = []
        for message in messages:
            items.extend([item for item in message.items if isinstance(item, FunctionResultContent)])

        return [
            StreamingChatMessageContent(
                role=AuthorRole.TOOL,
                name=name,
                items=items,
                choice_index=0,
                ai_model_id=ai_model_id,
                function_invoke_attempt=function_invoke_attempt,
            )
        ]

    @classmethod
    def _prepare_chat_history_for_request(
        cls: type[_T],
        chat_history: "ChatHistory",
    ) -> Any:
        """Prepare the chat history for a request.

        We must skip any items of type
        AnnotationContent, StreamingAnnotationContent, FileReferenceContent,
        or StreamingFileReferenceContent, and always map the role to either user,
        assistant, or developer.
        """
        response_inputs: list[Any] = []  # type: ignore
        for message in chat_history.messages:
            allowed_items = [
                i
                for i in message.items
                if not isinstance(
                    i,
                    (
                        AnnotationContent,
                        StreamingAnnotationContent,
                    ),
                )
            ]

            if not allowed_items:
                continue

            filtered_msg = ChatMessageContent(role=message.role, items=allowed_items)  # type: ignore
            original_role = message.role
            if original_role == AuthorRole.TOOL:
                original_role = AuthorRole.ASSISTANT
            contents: list[dict[str, Any]] = []

            for content in filtered_msg.items:
                match content:
                    case TextContent() | StreamingTextContent():
                        final_text = content.text
                        if not isinstance(final_text, str):
                            if isinstance(final_text, (list, tuple)):
                                final_text = " ".join(map(str, final_text))
                            else:
                                final_text = str(final_text)
                        text_type = "input_text" if original_role == AuthorRole.USER else "output_text"
                        contents.append({"type": text_type, "text": final_text})
                        response_inputs.append({"role": original_role, "content": contents})
                    case ImageContent():
                        image_url = ""
                        if content.data_uri:
                            image_url = content.data_uri
                        elif content.uri:
                            image_url = str(content.uri)

                        if not image_url:
                            ValueError("ImageContent must have either a data_uri or uri set to be used in the request.")

                        contents.append({"type": "input_image", "image_url": image_url})
                        response_inputs.append({"role": original_role, "content": contents})
                    case FunctionCallContent():
                        fc_dict = {
                            "type": "function_call",
                            "id": content.id,
                            "call_id": content.call_id,
                            "name": content.name,
                            "arguments": content.arguments,
                        }
                        response_inputs.append(fc_dict)
                    case FunctionResultContent():
                        rfrc_dict = {
                            "type": "function_call_output",
                            "output": str(content.result),
                            "call_id": content.call_id,
                        }
                        response_inputs.append(rfrc_dict)

        return response_inputs

    @classmethod
    def _get_tool_calls_from_output(cls: type[_T], output: list[ResponseFunctionToolCall]) -> list[FunctionCallContent]:
        """Get tool calls from a response output."""
        function_calls: list[FunctionCallContent] = []
        if not any(isinstance(i, ResponseFunctionToolCall) for i in output):
            return []
        for tool in cast(list[ResponseFunctionToolCall], output):
            content = tool if isinstance(tool, ResponseFunctionToolCall) else tool.delta
            function_calls.append(
                FunctionCallContent(
                    id=content.id,
                    call_id=content.call_id,
                    index=getattr(content, "index", None),
                    name=content.name,
                    arguments=content.arguments,
                )
            )
        return function_calls

    @classmethod
    def _get_metadata_from_response(cls: type[_T], response: Response | ResponseItem) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created_at if hasattr(response, "created_at") else None,
            "usage": response.usage.model_dump() if hasattr(response, "usage") and response.usage is not None else None,
        }

    @classmethod
    def _create_response_message_content(
        cls: type[_T],
        response: Response,
        ai_model_id: str | None = None,
        name: str | None = None,
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = cls._get_metadata_from_response(response)
        items = cls._collect_items_from_output(response.output)
        role_str = response.output[0].role if (response.output and hasattr(response.output[0], "role")) else "assistant"
        return ChatMessageContent(
            inner_content=response,
            ai_model_id=ai_model_id,
            metadata=metadata,
            name=name,
            role=AuthorRole(role_str),
            items=items,
            status=Status(response.status),
        )

    @classmethod
    def _create_response_message_content_for_response_item(
        cls: type[_T],
        response: ResponseItem,
        ai_model_id: str | None = None,
        name: str | None = None,
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = cls._get_metadata_from_response(response)
        items = cls._collect_items_for_response_item(response.content)  # type: ignore
        role_str = response.role if hasattr(response, "role") else "assistant"
        return ChatMessageContent(
            inner_content=response,
            ai_model_id=ai_model_id,
            metadata=metadata,
            name=name,
            role=AuthorRole(role_str),
            items=items,
            status=Status(response.status),
        )

    @classmethod
    def _create_output_item_done(
        cls: type[_T], agent: "OpenAIResponsesAgent", response: ResponseOutputItem
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata: dict[str, Any] = {}
        items: list[CMC_ITEM_TYPES] = []
        match response:
            case ResponseOutputMessage():
                items.extend(cls._collect_items_from_output([response]))

        # Determine role (if none is found, default to 'assistant')
        role_str = response.role if (response and hasattr(response, "role")) else "assistant"

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=agent.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role_str),
            items=items,
            status=Status(response.status),
        )

    @classmethod
    def _create_streaming_response_message_content(
        cls: type[_T],
        agent: "OpenAIResponsesAgent",
        response_content_part: ResponseContentPartAddedEvent,
    ) -> "StreamingChatMessageContent":
        """Create a streaming chat message content object from a choice."""
        # TODO(evmattso): add metadata support
        metadata: dict[str, Any] = {}
        from semantic_kernel.contents.streaming_chat_message_content import (
            StreamingChatMessageContent,
        )

        items = []
        if isinstance(response_content_part.part, ResponseOutputText):
            items.extend(cls._collect_text_and_annotations([response_content_part.part]))
        # TODO(evmatso): handle refusal
        return StreamingChatMessageContent(
            inner_content=response_content_part.part,
            name=agent.name,
            ai_model_id=agent.ai_model_id,
            metadata=metadata,
            role=AuthorRole("assistant"),
            items=items,
            choice_index=0,
        )

    @classmethod
    def _collect_items_from_output(cls: type[_T], output: list[Any]) -> list[Any]:
        """Aggregate items from the various output types."""
        items = []
        items.extend(cls._get_tool_calls_from_output(output))

        for msg in filter(lambda output_msg: isinstance(output_msg, (ResponseOutputMessage)), output or []):
            assert isinstance(msg, ResponseOutputMessage)  # nosec
            items.extend(cls._collect_text_and_annotations(msg.content))

        return items

    @classmethod
    def _collect_items_for_response_item(cls: type[_T], output: list[Any]) -> list[Any]:
        """Aggregate items from the various output types."""
        items = []
        items.extend(cls._get_tool_calls_from_output(output))

        for msg in filter(lambda msg: isinstance(msg, (ResponseInputText, ResponseOutputText)), output or []):
            if isinstance(msg, ResponseInputText):
                items.append(TextContent(text=msg.text))  # type: ignore
            if isinstance(msg, ResponseOutputText):
                items.extend(cls._collect_text_and_annotations([msg]))

        return items

    @classmethod
    def _collect_text_and_annotations(cls: type[_T], content_list: list[Any]) -> list[Any]:
        """Collect text content and annotation content from a single message's content."""
        collected: list[TextContent | AnnotationContent] = []
        for content in content_list:
            if isinstance(content, ResponseOutputText):
                collected.append(TextContent(text=content.text))
                if content.annotations:
                    for annotation in content.annotations:
                        collected.append(AnnotationContent(**annotation.model_dump()))
        return collected

    @classmethod
    async def _invoke_function_calls(
        cls: type[_T], kernel: "Kernel", fccs: list["FunctionCallContent"], chat_history: "ChatHistory"
    ) -> list[Any]:
        """Invoke the function calls."""
        tasks = [
            kernel.invoke_function_call(function_call=function_call, chat_history=chat_history)
            for function_call in fccs
        ]
        return await asyncio.gather(*tasks)

    @classmethod
    def _format_tool_outputs(
        cls: type[_T], fccs: list["FunctionCallContent"], chat_history: "ChatHistory"
    ) -> list[dict[str, str]]:
        """Format the tool outputs for submission."""
        tool_call_lookup = {
            tool_call.id: tool_call
            for message in chat_history.messages
            for tool_call in message.items
            if isinstance(tool_call, FunctionResultContent)
        }
        return [
            {"tool_call_id": fcc.id, "output": str(tool_call_lookup[fcc.id].result)}
            for fcc in fccs
            if fcc.id in tool_call_lookup
        ]

    @classmethod
    def _merge_options(
        cls: type[_T],
        *,
        agent: "OpenAIResponsesAgent",
        model: str | None = None,
        text: "ResponseTextConfigParam | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Merge run-time options with the agent-level options.

        Run-level parameters take precedence.
        """
        return {
            "model": model if model is not None else agent.ai_model_id,
            "text": text if text is not None else agent.text,
            "temperature": temperature if temperature is not None else agent.temperature,
            "top_p": top_p if top_p is not None else agent.top_p,
            "metadata": metadata if metadata is not None else agent.metadata,
            **kwargs,
        }

    @classmethod
    def _generate_options(cls: type[_T], **kwargs: Any) -> dict[str, Any]:
        """Generate a dictionary of options that can be passed directly to create_run."""
        merged = cls._merge_options(**kwargs)
        truncation = merged.get("truncation", None)
        max_output_tokens = merged.get("max_output_tokens", None)
        parallel_tool_calls = merged.get("parallel_tool_calls", None)
        return {
            "model": merged.get("model"),
            "top_p": merged.get("top_p"),
            "text": merged.get("text"),
            "temperature": merged.get("temperature"),
            "truncation": truncation,  # auto or disabled
            "metadata": merged.get("metadata"),
            "max_output_tokens": max_output_tokens,
            "parallel_tool_calls": parallel_tool_calls,
        }

    @classmethod
    def _get_tools(
        cls: type[_T],
        agent: "OpenAIResponsesAgent",
        kernel: "Kernel",
        function_choice_behavior: "FunctionChoiceBehavior",
    ) -> list[dict[str, str]]:
        """Get the list of tools for the assistant.

        Returns:
            The list of tools.
        """
        tools: list[Any] = []

        if agent.tools:
            tools.extend(agent.tools)

        # TODO(evmattso): make sure to respect filters on FCB
        if kernel.plugins:
            funcs = agent.kernel.get_full_list_of_function_metadata()
            tools.extend([kernel_function_metadata_to_response_function_call_format(f) for f in funcs])

        return tools

    # endregion
