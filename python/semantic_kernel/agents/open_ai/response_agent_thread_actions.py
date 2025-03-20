# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable
from functools import reduce
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar, cast

from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response import Response
from openai.types.responses.response_content_part_added_event import ResponseContentPartAddedEvent
from openai.types.responses.response_created_event import ResponseCreatedEvent
from openai.types.responses.response_error_event import ResponseErrorEvent
from openai.types.responses.response_function_call_arguments_delta_event import ResponseFunctionCallArgumentsDeltaEvent
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
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.response_function_result_content import ResponseFunctionResultContent
from semantic_kernel.contents.response_message_content import ResponseMessageContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_response_message_content import StreamingResponseMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.status import Status
from semantic_kernel.exceptions.agent_exceptions import (
    AgentInvokeException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from openai.types.responses.response_text_config_param import ResponseTextConfigParam
    from openai.types.responses.tool_param import ToolParam

    from semantic_kernel.agents.open_ai.openai_response_agent import OpenAIResponseAgent
    from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_call_content import FunctionCallContent
    from semantic_kernel.kernel import Kernel

_T = TypeVar("_T", bound="ResponseAgentThreadActions")

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class ResponseAgentThreadActions:
    """Response Agent Thread Actions class."""

    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "incomplete"]

    # region Invocation Methods

    @classmethod
    async def invoke(
        cls: type[_T],
        agent: "OpenAIResponseAgent",
        chat_history: "ChatHistory",
        *,
        # Run-level parameters:
        arguments: KernelArguments | None = None,
        function_choice_behavior: "FunctionChoiceBehavior | None" = None,
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

        for request_index in range(function_choice_behavior.maximum_auto_invoke_attempts):
            response: Response = await cls._get_response(
                agent=agent,
                chat_history=chat_history,
                merged_instructions=merged_instructions,
                tools=tools,
                response_options=response_options,
            )
            # response: Response = await agent.client.responses.create(
            #     input=cls._prepare_chat_history_for_request(chat_history),
            #     instructions=merged_instructions or agent.instructions,
            #     tools=tools,  # type: ignore
            #     **response_options,
            # )
            # assert response is not None  # nosec

            while response.status != "completed":
                # handle a timeout here...
                await asyncio.sleep(agent.polling_options.default_polling_interval.total_seconds())

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

            # Check if tool calls are required
            function_calls = cls._get_tool_calls_from_output(response.output)
            if (fc_count := len(function_calls)) == 0:
                yield True, cls._create_response_message_content(agent, response)
                break

            response_message = cls._create_response_message_content(agent, response)
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
                        is_response_api=True,
                    )
                    for function_call in function_calls
                ],
            )

            if any(result.terminate for result in results if result is not None):
                for msg in merge_function_results(chat_history.messages[-len(results) :]):
                    yield True, msg
        else:
            pass
            # Do a final call, without function calling when the max has been reached.
            function_choice_behavior = FunctionChoiceBehavior.NoneInvoke()
            response: Response = await cls._get_response(
                agent=agent,
                chat_history=chat_history,
                merged_instructions=merged_instructions,
                tools=tools,
                response_options=response_options,
            )
            yield True, cls._create_response_message_content(agent, response)

    @classmethod
    async def _get_response(
        cls: type[_T],
        agent: "OpenAIResponseAgent",
        chat_history: "ChatHistory",
        merged_instructions: str | None = None,
        tools: Any | None = None,
        response_options: dict | None = None,
        stream: bool = False,
    ) -> None:
        response: Response = await agent.client.responses.create(
            input=cls._prepare_chat_history_for_request(chat_history),
            instructions=merged_instructions or agent.instructions,
            tools=tools,  # type: ignore
            stream=stream,
            **response_options,
        )
        assert response is not None  # nosec
        return response

    @classmethod
    async def invoke_stream(
        cls: type[_T],
        agent: "OpenAIResponseAgent",
        chat_history: "ChatHistory",
        *,
        # Run-level parameters:
        arguments: KernelArguments | None = None,
        function_choice_behavior: "FunctionChoiceBehavior | None" = None,
        include: list[
            Literal[
                "file_search_call.results", "message.input_image.image_url", "computer_call_output.output.image_url"
            ]
        ]
        | None = None,
        instructions_override: str | None = None,
        kernel: "Kernel | None" = None,
        max_output_tokens: int | None = None,
        messages: list["ChatMessageContent"] | None = None,
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
    ) -> AsyncIterable["StreamingResponseMessageContent"]:
        """Invoke the assistant.

        Args:
            agent: The assistant agent.
            chat_history: The Chat History to use for input.
            thread_id: The thread ID.
            arguments: The kernel arguments.
            kernel: The kernel.
            function_choice_behavior: The function choice behavior.
            include: Additional output data to include in the response.
            instructions_override: The instructions override.
            max_output_tokens: The maximum completion tokens.
            messages: The messages to include in the request.
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

        for request_index in range(function_choice_behavior.maximum_auto_invoke_attempts):
            response: Response = await cls._get_response(
                agent=agent,
                chat_history=chat_history,
                merged_instructions=merged_instructions,
                tools=tools,
                response_options=response_options,
                stream=True,
            )

            all_messages: list[StreamingResponseMessageContent] = []
            function_call_returned = False

            async with response as response_stream:
                async for event in response_stream:
                    event = cast(ResponseStreamEvent, event)
                    match event:
                        case ResponseCreatedEvent():
                            logger.debug(f"Agent response created with ID: {event.response.id}")
                        case ResponseOutputItemAddedEvent():
                            function_calls = cls._get_tool_calls_from_output([event.item])
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
                            msg = cls._create_output_item_done(agent, event.item)
                            if messages is not None:
                                messages.append(msg)
                        case ResponseErrorEvent():
                            logger.error(
                                f"Error in agent invoke_stream: {event.message} "
                                f"(code: {event.code if event.code else 'unknown'})"
                            )
                            break

            if not function_call_returned:
                return

            full_completion: StreamingResponseMessageContent = reduce(lambda x, y: x + y, all_messages)
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
                        is_response_api=True,
                    )
                    for function_call in function_calls
                ],
            )

            # Merge and yield the function results, regardless of the termination status
            # Include the ai_model_id so we can later add two streaming messages together
            # Some settings may not have an ai_model_id, so we need to check for it
            function_result_messages = cls._merge_streaming_function_results(
                messages=chat_history.messages[-len(results) :],
                name=agent.name,
                ai_model_id=agent.ai_model_id,  # type: ignore
                function_invoke_attempt=request_index,
            )
            if cls._yield_function_result_messages(function_result_messages):
                yield function_result_messages[0]

            if any(result.terminate for result in results if result is not None):
                break

    # endregion

    # region Helper Methods

    @classmethod
    def _build_streaming_msg(
        cls: type[_T],
        *,
        agent: "OpenAIResponseAgent",
        metadata: dict[str, str] | None,
        event: ResponseStreamEvent,
        items: list[Any],
        choice_index: int,
        role: str = "assistant",
    ) -> StreamingResponseMessageContent:
        """Helper to create StreamingResponseMessageContent."""
        return StreamingResponseMessageContent(
            inner_content=event,
            ai_model_id=agent.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role),
            items=items,
            choice_index=choice_index,
            name=agent.name,
        )

    @classmethod
    def _yield_function_result_messages(cls: type[_T], function_result_messages: list) -> bool:
        """Determine if the function result messages should be yielded.

        If there are messages and if the first message has items, then yield the messages.
        """
        return len(function_result_messages) > 0 and len(function_result_messages[0].items) > 0

    @classmethod
    def _merge_streaming_function_results(
        cls: type[_T],
        messages: list["ResponseMessageContent | StreamingResponseMessageContent"],
        name: str,
        ai_model_id: str | None = None,
        function_invoke_attempt: int | None = None,
    ) -> list["StreamingResponseMessageContent"]:
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
            StreamingResponseMessageContent(
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
        role_key: str = "role",
        content_key: str = "content",
    ) -> Any:
        """Prepare the chat history for a request.

        We must skip any items of type
        AnnotationContent, StreamingAnnotationContent, FileReferenceContent,
        or StreamingFileReferenceContent, and always map the role to either user,
        assistant, or developer.
        """
        response_inputs = []
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

            filtered_msg = ResponseMessageContent(role=message.role, items=allowed_items)
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
                    case ResponseFunctionResultContent():
                        rfrc_dict = {
                            "type": "function_call_output",
                            "output": str(content.result),
                            "call_id": content.id or "",
                        }
                        response_inputs.append(rfrc_dict)

        return response_inputs

    @classmethod
    def _get_tool_calls_from_output(
        cls: type[_T], output: list[ResponseFunctionToolCall | ResponseFunctionCallArgumentsDeltaEvent]
    ) -> list[FunctionCallContent]:
        """Get tool calls from a response output."""
        function_calls: list[FunctionCallContent] = []
        if not any(isinstance(i, (ResponseFunctionToolCall, ResponseFunctionCallArgumentsDeltaEvent)) for i in output):
            return []
        for tool in cast(list[ResponseFunctionToolCall] | list[ResponseFunctionCallArgumentsDeltaEvent], output):
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
    def _get_metadata_from_response(cls: type[_T], response: Response) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created_at,
            "usage": response.usage.model_dump() if response.usage is not None else None,
        }

    @classmethod
    def _create_response_message_content(
        cls: type[_T],
        agent: "OpenAIResponseAgent",
        response: Response,
    ) -> "ResponseMessageContent":
        """Create a chat message content object from a choice."""
        metadata = cls._get_metadata_from_response(response)
        items = cls._collect_items_from_output(response.output)
        role_str = response.output[0].role if (response.output and hasattr(response.output[0], "role")) else "assistant"
        return ResponseMessageContent(
            inner_content=response,
            ai_model_id=agent.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role_str),
            items=items,
            status=Status(response.status),
        )

    @classmethod
    def _create_output_item_done(
        cls: type[_T], agent: "OpenAIResponseAgent", response: ResponseOutputItem
    ) -> "ResponseMessageContent":
        """Create a chat message content object from a choice."""
        metadata = {}
        items = []
        match response:
            case ResponseOutputMessage():
                items.extend(cls._collect_items_from_output([response]))

        # Determine role (if none is found, default to 'assistant')
        role_str = response.role if (response and hasattr(response, "role")) else "assistant"

        return ResponseMessageContent(
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
        agent: "OpenAIResponseAgent",
        response_content_part: ResponseContentPartAddedEvent,
    ) -> "StreamingResponseMessageContent":
        """Create a streaming chat message content object from a choice."""
        # metadata = cls._get_metadata_from_response(response)
        metadata = {}
        from semantic_kernel.contents.streaming_response_message_content import (
            StreamingResponseMessageContent,
        )

        items = []
        if isinstance(response_content_part.part, ResponseOutputText):
            items.extend(cls._collect_text_and_annotations([response_content_part.part]))
        # TODO handle refusal
        return StreamingResponseMessageContent(
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
    def _collect_text_and_annotations(cls: type[_T], content_list: list[Any]) -> list[Any]:
        """Collect text content and annotation content from a single message's content."""
        collected = []
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
        agent: "OpenAIResponseAgent",
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
            "text": text if text is not None else None,
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
        agent: "OpenAIResponseAgent",
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


# def store_response_usage(self, response: Response) -> None:
#     """Retrieve and aggregate usage data from the response object.

#     Tracking attributes (`prompt_tokens`, `completion_tokens`, `total_tokens`) and
#     instantiate or update the `response_usage` model with the same data.
#     """
#     # 1. Ensure the response has a usage attribute and it's not empty.
#     usage_data = getattr(response, "usage", None)
#     if not usage_data:
#         return  # No usage info to store

#     # 2. Convert to dict if needed; handle both dict-like and Pydantic model usage structures.
#     if not isinstance(usage_data, dict):
#         # If `response.usage` is already a pydantic model, we can use `.dict()`.
#         usage_data = usage_data.dict()

#     # 3. Parse the raw usage data into our strongly-typed `ResponseUsage` model.
#     usage_obj = ResponseUsage(**usage_data)

#     # 4. Either set or update the handler's `response_usage`.
#     if self.response_usage is None:
#         self.response_usage = usage_obj
#     else:
#         # If you already have a `response_usage`, you could aggregate further
#         # or overwrite, depending on your desired logic. Below is an example of
#         # adding the token counts together if you wish to accumulate usage over time.
#         self.response_usage.input_tokens += usage_obj.input_tokens
#         self.response_usage.output_tokens += usage_obj.output_tokens
#         self.response_usage.total_tokens += usage_obj.total_tokens
#         self.response_usage.input_tokens_details.cached_tokens += usage_obj.input_tokens_details.cached_tokens
#         self.response_usage.output_tokens_details.reasoning_tokens += usage_obj.output_tokens_details.reasoning_tokens

#     # 5. Update the overarching usage counters in the handler.
#     self.prompt_tokens += usage_obj.input_tokens
#     self.completion_tokens += usage_obj.output_tokens
#     self.total_tokens += usage_obj.total_tokens

#     # 6. (Optional) Log the stored usage data with relevant details for traceability.
#     logger.info(
#         f"OpenAI usage stored. "
#         f"Prompt tokens: {self.prompt_tokens}, "
#         f"Completion tokens: {self.completion_tokens}, "
#         f"Total tokens: {self.total_tokens}"
#     )
