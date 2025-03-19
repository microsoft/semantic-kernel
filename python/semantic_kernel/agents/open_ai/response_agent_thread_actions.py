# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable, Iterable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar, cast

from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.computer_tool import ComputerTool
from openai.types.responses.file_search_tool import FileSearchTool
from openai.types.responses.response import Response
from openai.types.responses.response_function_call_arguments_delta_event import ResponseFunctionCallArgumentsDeltaEvent
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from openai.types.responses.web_search_tool import WebSearchTool

from semantic_kernel.agents.open_ai.assistant_content_generation import (
    generate_final_streaming_message_content,
    generate_function_call_streaming_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_function_content,
    generate_streaming_message_content,
    get_function_call_contents,
)
from semantic_kernel.agents.open_ai.function_action_result import FunctionActionResult
from semantic_kernel.connectors.ai.function_calling_utils import (
    kernel_function_metadata_to_response_function_call_format,
    merge_function_results,
    merge_streaming_function_results,
)
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.response_function_result_content import ResponseFunctionResultContent
from semantic_kernel.contents.response_message_content import ResponseMessageContent
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
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel import Kernel

_T = TypeVar("_T", bound="ResponseAgentThreadActions")

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class ResponseAgentThreadActions:
    """Response Agent Thread Actions class."""

    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "incomplete"]

    tool_metadata: ClassVar[dict[str, Sequence[Any]]] = {
        "file_search": [{"type": "file_search"}],
        "web_search": [{"type": "web_search_preview"}],
    }

    # region Invocation Methods

    @classmethod
    async def invoke(
        cls: type[_T],
        agent: "OpenAIResponseAgent",
        chat_history: "ChatHistory",
        *,
        # Run-level parameters:
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        function_choice_behavior: "FunctionChoiceBehavior | None" = None,
        instructions_override: str | None = None,
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
            response: Response = await agent.client.responses.create(
                input=cls._prepare_chat_history_for_request(chat_history),
                instructions=merged_instructions or agent.instructions,
                tools=tools,  # type: ignore
                **response_options,
            )
            assert response is not None  # nosec

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
            # self._reset_function_choice_settings(settings)
            # return await self._inner_get_chat_message_contents(chat_history, settings)

    @classmethod
    async def invoke_stream(
        cls: type[_T],
        agent: "OpenAIResponseAgent",
        chat_history: "ChatHistory",
        *,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        function_choice_behavior: "FunctionChoiceBehavior | None" = None,
        instructions_override: str | None = None,
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
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the assistant.

        Args:
            agent: The assistant agent.
            thread_id: The thread ID.
            arguments: The kernel arguments.
            kernel: The kernel.
            function_choice_behavior: The function choice behavior.
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

        tools = cls._get_tools(agent=agent, kernel=kernel)  # type: ignore

        base_instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        merged_instructions: str = (
            instructions_override if instructions_override is not None else base_instructions or ""
        )

        # form response options
        response_options = cls._generate_options(
            agent=agent,
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

        stream = await agent.client.responses.create(
            input=cls._prepare_chat_history_for_request(chat_history),
            instructions=merged_instructions or agent.instructions,
            tools=tools,  # type: ignore
            stream=True,
            **response_options,
        )

        function_steps: dict[str, "FunctionCallContent"] = {}
        active_messages: dict[str, RunStep] = {}

        while True:
            async with stream as response_stream:
                async for event in response_stream:
                    if event.event == "thread.run.created":
                        run = event.data
                        logger.info(f"Assistant run created with ID: {run.id}")
                    elif event.event == "thread.run.in_progress":
                        run = event.data
                        logger.info(f"Assistant run in progress with ID: {run.id}")
                    elif event.event == "thread.message.delta":
                        content = generate_streaming_message_content(agent.name, event.data)
                        yield content
                    elif event.event == "thread.run.step.completed":
                        step_completed = cast(RunStep, event.data)
                        logger.info(f"Run step completed with ID: {event.data.id}")
                        if isinstance(step_completed.step_details, MessageCreationStepDetails):
                            message_id = step_completed.step_details.message_creation.message_id
                            if message_id not in active_messages:
                                active_messages[message_id] = event.data
                    elif event.event == "thread.run.step.delta":
                        run_step_event: RunStepDeltaEvent = event.data
                        details = run_step_event.delta.step_details
                        if not details:
                            continue
                        step_details = event.data.delta.step_details
                        if isinstance(details, ToolCallDeltaObject) and details.tool_calls:
                            for tool_call in details.tool_calls:
                                tool_content = None
                                if tool_call.type == "function":
                                    tool_content = generate_streaming_function_content(agent.name, step_details)
                                elif tool_call.type == "code_interpreter":
                                    tool_content = generate_streaming_code_interpreter_content(agent.name, step_details)
                                if tool_content:
                                    yield tool_content
                    elif event.event == "thread.run.requires_action":
                        run = event.data
                        function_action_result = await cls._handle_streaming_requires_action(
                            agent.name, kernel, run, function_steps
                        )
                        if function_action_result is None:
                            raise AgentInvokeException(
                                f"Function call required but no function steps found for agent `{agent.name}` "
                                f"thread: {thread_id}."
                            )
                        if function_action_result.function_result_streaming_content:
                            # Yield the function result content to the caller
                            yield function_action_result.function_result_streaming_content
                            if messages is not None:
                                # Add the function result content to the messages list, if it exists
                                messages.append(function_action_result.function_result_streaming_content)
                        if function_action_result.function_call_streaming_content:
                            if messages is not None:
                                messages.append(function_action_result.function_call_streaming_content)
                            stream = agent.client.beta.threads.runs.submit_tool_outputs_stream(
                                run_id=run.id,
                                thread_id=thread_id,
                                tool_outputs=function_action_result.tool_outputs,  # type: ignore
                            )
                            break
                    elif event.event == "thread.run.completed":
                        run = event.data
                        logger.info(f"Run completed with ID: {run.id}")
                        if len(active_messages) > 0:
                            for id in active_messages:
                                step: RunStep = active_messages[id]
                                message = await cls._retrieve_message(
                                    agent=agent,
                                    thread_id=thread_id,
                                    message_id=id,  # type: ignore
                                )

                                if message and message.content:
                                    content = generate_final_streaming_message_content(agent.name, message, step)
                                    if messages is not None:
                                        messages.append(content)
                        return
                    elif event.event == "thread.run.failed":
                        run = event.data  # type: ignore
                        error_message = ""
                        if run.last_error and run.last_error.message:
                            error_message = run.last_error.message
                        raise AgentInvokeException(
                            f"Run failed with status: `{run.status}` for agent `{agent.name}` and thread `{thread_id}` "
                            f"with error: {error_message}"
                        )
                else:
                    # If the inner loop completes without encountering a 'break', exit the outer loop
                    break

    @classmethod
    async def _handle_streaming_requires_action(
        cls: type[_T],
        agent_name: str,
        kernel: "Kernel",
        run: "Run",
        function_steps: dict[str, "FunctionCallContent"],
        **kwargs: Any,
    ) -> FunctionActionResult | None:
        """Handle the requires action event for a streaming run."""
        fccs = get_function_call_contents(run, function_steps)
        if fccs:
            function_call_streaming_content = generate_function_call_streaming_content(agent_name=agent_name, fccs=fccs)
            from semantic_kernel.contents.chat_history import ChatHistory

            chat_history = ChatHistory() if kwargs.get("chat_history") is None else kwargs["chat_history"]
            _ = await cls._invoke_function_calls(kernel=kernel, fccs=fccs, chat_history=chat_history)
            function_result_streaming_content = merge_streaming_function_results(chat_history.messages)[0]
            tool_outputs = cls._format_tool_outputs(fccs, chat_history)
            return FunctionActionResult(
                function_call_streaming_content, function_result_streaming_content, tool_outputs
            )
        return None

    # endregion

    @classmethod
    def _prepare_chat_history_for_request(
        cls: type[_T],
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> Any:
        """Prepare the chat history for a request into new Responses format."""
        # if self.instruction_role == "developer" and message.to_dict(role_key=role_key)[role_key] == "system"
        result = []
        for message in chat_history.messages:
            if isinstance(message, (AnnotationContent, FileReferenceContent)):
                continue
            d = message.to_dict(role_key=role_key, content_key=content_key)
            r = d.get(role_key)
            if r == "assistant" and any(isinstance(i, FunctionCallContent) for i in message.items):
                for item in message.items:
                    if isinstance(item, FunctionCallContent):
                        fc_dict = {
                            "type": "function_call",
                            "id": item.id,
                            "call_id": item.call_id,
                            "name": item.name,
                            "arguments": item.arguments,
                        }
                        result.append(fc_dict)
            elif r == "tool" and any(isinstance(i, ResponseFunctionResultContent) for i in message.items):
                for item in message.items:
                    if isinstance(item, ResponseFunctionResultContent):
                        fco_dict = {
                            "type": "function_call_output",
                            "output": str(item.result),
                            "call_id": item.id or "",
                        }
                        result.append(fco_dict)
            else:
                d.pop("tool_calls", None)
                result.append(d)
        return result

    @classmethod
    def _get_tool_calls_from_output(
        cls: type[_T], output: ResponseFunctionToolCall | ResponseFunctionCallArgumentsDeltaEvent
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

        # Collect all items (tool calls, text content, annotations) into a single list
        # items = []
        # for output in response.output:
        #    items.extend(cls._collect_items_from_output(output))
        items = cls._collect_items_from_output(response.output)

        # Determine role (if none is found, default to 'assistant')
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
        from semantic_kernel.contents.function_result_content import FunctionResultContent

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
    def _get_metadata(cls: type[_T], message: "ChatMessageContent") -> dict[str, str]:
        """Get the metadata for an agent message."""
        return {k: str(v) if v is not None else "" for k, v in (message.metadata or {}).items()}

    @classmethod
    def _get_tool_definition(cls: type[_T], tools: list[Any]) -> Iterable[Any]:
        if not tools:
            return
        for tool in tools:
            if tool_definition := cls.tool_metadata.get(tool):
                yield from tool_definition

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

        for tool in agent.tools:
            if isinstance(tool, FileSearchTool):
                tools.append({"type": "file_search"})
            elif isinstance(tool, WebSearchTool):
                tools.append({"type": "web_search_preview"})
            elif isinstance(tool, ComputerTool):
                tools.append({"type": "computer_use_preview"})  # TODO handle this case

        # TODO(evmattso): make sure to respect filters on FCB
        if kernel.plugins:
            funcs = agent.kernel.get_full_list_of_function_metadata()
            tools.extend([kernel_function_metadata_to_response_function_call_format(f) for f in funcs])

        return tools
