# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable, Iterable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar, cast

from openai import NOT_GIVEN, AsyncOpenAI, NotGiven
from openai.types.beta.code_interpreter_tool import CodeInterpreterTool
from openai.types.beta.file_search_tool import FileSearchTool
from openai.types.beta.threads.run_create_params import AdditionalMessage, AdditionalMessageAttachment
from openai.types.beta.threads.runs import (
    MessageCreationStepDetails,
    RunStep,
    RunStepDeltaEvent,
    ToolCallDeltaObject,
    ToolCallsStepDetails,
)

from semantic_kernel.agents.open_ai.assistant_content_generation import (
    generate_code_interpreter_content,
    generate_final_streaming_message_content,
    generate_function_call_content,
    generate_function_call_streaming_content,
    generate_function_result_content,
    generate_message_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_function_content,
    generate_streaming_message_content,
    get_function_call_contents,
    get_message_contents,
    merge_streaming_function_results,
)
from semantic_kernel.agents.open_ai.function_action_result import FunctionActionResult
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from openai.types.beta.assistant_response_format_option_param import AssistantResponseFormatOptionParam
    from openai.types.beta.assistant_tool_param import AssistantToolParam
    from openai.types.beta.threads.message import Message
    from openai.types.beta.threads.run import Run
    from openai.types.beta.threads.run_create_params import AdditionalMessageAttachmentTool, TruncationStrategy

    from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_call_content import FunctionCallContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
        AutoFunctionInvocationContext,
    )
    from semantic_kernel.kernel import Kernel

_T = TypeVar("_T", bound="AssistantThreadActions")

logger: logging.Logger = logging.getLogger(__name__)


@release_candidate
class AssistantThreadActions:
    """Assistant Thread Actions class."""

    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "cancelled", "expired", "incomplete"]

    tool_metadata: ClassVar[dict[str, Sequence[Any]]] = {
        "file_search": [{"type": "file_search"}],
        "code_interpreter": [{"type": "code_interpreter"}],
    }

    # region Messaging Handling Methods

    @classmethod
    async def create_message(
        cls: type[_T],
        client: "AsyncOpenAI",
        thread_id: str,
        message: "str | ChatMessageContent",
        allowed_message_roles: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> "Message | None":
        """Create a message in the thread.

        Args:
            client: The client to use to create the message.
            thread_id: The ID of the thread to create the message in.
            message: The message to create.
            allowed_message_roles: The allowed message roles.
                Defaults to [AuthorRole.USER, AuthorRole.ASSISTANT] if None.
                Providing an empty list will disallow all message roles.
            kwargs: Additional keyword arguments.

        Returns:
            The created message.
        """
        from semantic_kernel.contents.chat_message_content import ChatMessageContent

        if isinstance(message, str):
            message = ChatMessageContent(role=AuthorRole.USER, content=message)

        if any(isinstance(item, FunctionCallContent) for item in message.items):
            return None

        # Set the default allowed message roles if not provided
        if allowed_message_roles is None:
            allowed_message_roles = [AuthorRole.USER, AuthorRole.ASSISTANT]
        if message.role.value not in allowed_message_roles and message.role != AuthorRole.TOOL:
            raise AgentExecutionException(
                f"Invalid message role `{message.role.value}`. Allowed roles are {allowed_message_roles}."
            )

        message_contents: list[dict[str, Any]] = get_message_contents(message=message)

        return await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="assistant" if message.role == AuthorRole.TOOL else message.role.value,  # type: ignore
            content=message_contents,  # type: ignore
            **kwargs,
        )

    # endregion

    # region Invocation Methods

    @classmethod
    async def invoke(
        cls: type[_T],
        *,
        agent: "OpenAIAssistantAgent",
        thread_id: str,
        additional_instructions: str | None = None,
        additional_messages: "list[ChatMessageContent] | None" = None,
        arguments: KernelArguments | None = None,
        instructions_override: str | None = None,
        kernel: "Kernel | None" = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        polling_options: RunPollingOptions | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the assistant.

        Args:
            agent: The assistant agent.
            thread_id: The thread ID.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: The additional instructions.
            additional_messages: The additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: The parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            polling_options: The polling options defined at the run-level. These will override the agent-level
                polling options.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of tuple of the visibility of the message and the chat message content.
        """
        arguments = KernelArguments() if arguments is None else KernelArguments(**arguments, **kwargs)
        kernel = kernel or agent.kernel

        tools = cls._get_tools(agent=agent, kernel=kernel)  # type: ignore

        base_instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        merged_instructions: str = ""
        if instructions_override is not None:
            merged_instructions = instructions_override
        elif base_instructions and additional_instructions:
            merged_instructions = f"{base_instructions}\n\n{additional_instructions}"
        else:
            merged_instructions = base_instructions or additional_instructions or ""

        # form run options
        run_options = cls._generate_options(
            agent=agent,
            model=model,
            response_format=response_format,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            parallel_tool_calls_enabled=parallel_tool_calls,
            truncation_message_count=truncation_strategy,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            additional_messages=additional_messages,
            reasoning_effort=reasoning_effort,
        )

        run_options = {k: v for k, v in run_options.items() if v is not None}

        run = await agent.client.beta.threads.runs.create(
            assistant_id=agent.id,
            thread_id=thread_id,
            instructions=merged_instructions or agent.instructions,
            tools=tools,  # type: ignore
            **run_options,
        )

        processed_step_ids = set()
        function_steps: dict[str, "FunctionCallContent"] = {}

        while run.status != "completed":
            run = await cls._poll_run_status(
                agent=agent, run=run, thread_id=thread_id, polling_options=polling_options or agent.polling_options
            )

            if run.status in cls.error_message_states:
                error_message = ""
                if run.last_error and run.last_error.message:
                    error_message = run.last_error.message
                incomplete_details = ""
                if run.incomplete_details:
                    incomplete_details = str(run.incomplete_details.reason)
                raise AgentInvokeException(
                    f"Run failed with status: `{run.status}` for agent `{agent.name}` and thread `{thread_id}` "
                    f"with error: {error_message} or incomplete details: {incomplete_details}"
                )

            # Check if function calling required
            if run.status == "requires_action":
                logger.debug(f"Run [{run.id}] requires action for agent `{agent.name}` and thread `{thread_id}`")
                fccs = get_function_call_contents(run, function_steps)
                if fccs:
                    logger.debug(
                        f"Yielding `generate_function_call_content` for agent `{agent.name}` and "
                        f"thread `{thread_id}`, visibility False"
                    )
                    yield False, generate_function_call_content(agent_name=agent.name, fccs=fccs)

                    from semantic_kernel.contents.chat_history import ChatHistory

                    chat_history = ChatHistory()
                    _ = await cls._invoke_function_calls(
                        kernel=kernel, fccs=fccs, chat_history=chat_history, arguments=arguments
                    )

                    tool_outputs = cls._format_tool_outputs(fccs, chat_history)
                    await agent.client.beta.threads.runs.submit_tool_outputs(
                        run_id=run.id,
                        thread_id=thread_id,
                        tool_outputs=tool_outputs,  # type: ignore
                    )
                    logger.debug(f"Submitted tool outputs for agent `{agent.name}` and thread `{thread_id}`")
                    continue

            steps_response = await agent.client.beta.threads.runs.steps.list(run_id=run.id, thread_id=thread_id)
            logger.debug(f"Called for steps_response for run [{run.id}] agent `{agent.name}` and thread `{thread_id}`")
            steps: list[RunStep] = steps_response.data

            def sort_key(step: RunStep):
                # Put tool_calls first, then message_creation
                # If multiple steps share a type, break ties by completed_at
                return (0 if step.type == "tool_calls" else 1, step.completed_at)

            completed_steps_to_process = sorted(
                [s for s in steps if s.completed_at is not None and s.id not in processed_step_ids], key=sort_key
            )

            logger.debug(
                f"Completed steps to process for run [{run.id}] agent `{agent.name}` and thread `{thread_id}` "
                f"with length `{len(completed_steps_to_process)}`"
            )

            message_count = 0
            for completed_step in completed_steps_to_process:
                if completed_step.type == "tool_calls":
                    logger.debug(
                        f"Entering step type tool_calls for run [{run.id}], agent `{agent.name}` and "
                        f"thread `{thread_id}`"
                    )
                    assert hasattr(completed_step.step_details, "tool_calls")  # nosec
                    tool_call_details = cast(ToolCallsStepDetails, completed_step.step_details)
                    for tool_call in tool_call_details.tool_calls:
                        is_visible = False
                        content: "ChatMessageContent | None" = None
                        if tool_call.type == "code_interpreter":
                            logger.debug(
                                f"Entering step type tool_calls for run [{run.id}], [code_interpreter] for "
                                f"agent `{agent.name}` and thread `{thread_id}`"
                            )
                            content = generate_code_interpreter_content(
                                agent.name,
                                tool_call.code_interpreter.input,  # type: ignore
                            )
                            is_visible = True
                        elif tool_call.type == "function":
                            logger.debug(
                                f"Entering step type tool_calls for run [{run.id}], [function] for agent "
                                f"`{agent.name}` and thread `{thread_id}`"
                            )
                            function_step = function_steps.get(tool_call.id)
                            assert function_step is not None  # nosec
                            content = generate_function_result_content(
                                agent_name=agent.name, function_step=function_step, tool_call=tool_call
                            )

                        if content:
                            message_count += 1
                            logger.debug(
                                f"Yielding tool_message for run [{run.id}], agent `{agent.name}` and thread "
                                f"`{thread_id}` and message count `{message_count}`, is_visible `{is_visible}`"
                            )
                            yield is_visible, content
                elif completed_step.type == "message_creation":
                    logger.debug(
                        f"Entering step type message_creation for run [{run.id}], agent `{agent.name}` and "
                        f"thread `{thread_id}`"
                    )
                    message = await cls._retrieve_message(
                        agent=agent,
                        thread_id=thread_id,
                        message_id=completed_step.step_details.message_creation.message_id,  # type: ignore
                    )
                    if message:
                        content = generate_message_content(agent.name, message, completed_step)
                        if content and len(content.items) > 0:
                            message_count += 1
                            logger.debug(
                                f"Yielding message_creation for run [{run.id}], agent `{agent.name}` and "
                                f"thread `{thread_id}` and message count `{message_count}`, is_visible `{True}`"
                            )
                            yield True, content
                processed_step_ids.add(completed_step.id)

    @classmethod
    async def invoke_stream(
        cls: type[_T],
        *,
        agent: "OpenAIAssistantAgent",
        thread_id: str,
        additional_instructions: str | None = None,
        additional_messages: "list[ChatMessageContent] | None" = None,
        arguments: KernelArguments | None = None,
        instructions_override: str | None = None,
        kernel: "Kernel | None" = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        output_messages: list["ChatMessageContent"] | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the assistant.

        Args:
            agent: The assistant agent.
            thread_id: The thread ID.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: The additional instructions.
            additional_messages: The additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            messages: The messages that act as a receiver for completed messages.
            metadata: The metadata.
            model: The model.
            output_messages: The output messages received from the agent. These are full content messages
                formed from the streamed chunks.
            parallel_tool_calls: The parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of StreamingChatMessageContent.
        """
        arguments = KernelArguments() if arguments is None else KernelArguments(**arguments, **kwargs)
        kernel = kernel or agent.kernel

        tools = cls._get_tools(agent=agent, kernel=kernel)  # type: ignore

        base_instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        merged_instructions: str = ""
        if instructions_override is not None:
            merged_instructions = instructions_override
        elif base_instructions and additional_instructions:
            merged_instructions = f"{base_instructions}\n\n{additional_instructions}"
        else:
            merged_instructions = base_instructions or additional_instructions or ""

        # form run options
        run_options = cls._generate_options(
            agent=agent,
            model=model,
            response_format=response_format,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            parallel_tool_calls_enabled=parallel_tool_calls,
            truncation_message_count=truncation_strategy,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            additional_messages=additional_messages,
            reasoning_effort=reasoning_effort,
        )

        run_options = {k: v for k, v in run_options.items() if v is not None}

        stream = agent.client.beta.threads.runs.stream(
            assistant_id=agent.id,
            thread_id=thread_id,
            instructions=merged_instructions or agent.instructions,
            tools=tools,  # type: ignore
            **run_options,
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
                                content_is_visible = False
                                if tool_call.type == "function":
                                    tool_content = generate_streaming_function_content(agent.name, step_details)
                                elif tool_call.type == "code_interpreter":
                                    tool_content = generate_streaming_code_interpreter_content(agent.name, step_details)
                                    content_is_visible = True
                                if tool_content:
                                    if output_messages is not None:
                                        output_messages.append(tool_content)
                                    if content_is_visible:
                                        yield tool_content
                    elif event.event == "thread.run.requires_action":
                        run = event.data
                        function_action_result = await cls._handle_streaming_requires_action(
                            agent.name,
                            kernel,
                            run,
                            function_steps,
                            arguments,
                        )
                        if function_action_result is None:
                            raise AgentInvokeException(
                                f"Function call required but no function steps found for agent `{agent.name}` "
                                f"thread: {thread_id}."
                            )
                        if function_action_result.function_call_streaming_content:
                            if output_messages is not None:
                                output_messages.append(function_action_result.function_call_streaming_content)
                            stream = agent.client.beta.threads.runs.submit_tool_outputs_stream(
                                run_id=run.id,
                                thread_id=thread_id,
                                tool_outputs=function_action_result.tool_outputs,  # type: ignore
                            )
                        if function_action_result.function_result_streaming_content and output_messages is not None:
                            # Add the function result content to the messages list, if it exists
                            output_messages.append(function_action_result.function_result_streaming_content)
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
                                    if output_messages is not None:
                                        output_messages.append(content)
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
        arguments: KernelArguments,
        **kwargs: Any,
    ) -> FunctionActionResult | None:
        """Handle the requires action event for a streaming run."""
        fccs = get_function_call_contents(run, function_steps)
        if fccs:
            function_call_streaming_content = generate_function_call_streaming_content(agent_name=agent_name, fccs=fccs)
            from semantic_kernel.contents.chat_history import ChatHistory

            chat_history = ChatHistory() if kwargs.get("chat_history") is None else kwargs["chat_history"]
            results = await cls._invoke_function_calls(
                kernel=kernel, fccs=fccs, chat_history=chat_history, arguments=arguments
            )

            function_result_streaming_content = merge_streaming_function_results(
                messages=chat_history.messages[-len(results) :],
                name=agent_name,
            )
            tool_outputs = cls._format_tool_outputs(fccs, chat_history)
            return FunctionActionResult(
                function_call_streaming_content,
                function_result_streaming_content,
                tool_outputs,
            )
        return None

    # endregion

    @classmethod
    async def get_messages(
        cls: type[_T],
        client: AsyncOpenAI,
        thread_id: str,
        sort_order: Literal["asc", "desc"] | None = None,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Get messages from the thread.

        Args:
            client: The client to use to get the messages.
            thread_id: The ID of the thread to get the messages from.
            sort_order: The sort order of the messages.

        Returns:
            An async iterable of ChatMessageContent.
        """
        agent_names: dict[str, Any] = {}
        last_id: str | NotGiven = NOT_GIVEN

        while True:
            messages = await client.beta.threads.messages.list(
                thread_id=thread_id,
                order=sort_order,  # type: ignore
                after=last_id,
            )

            if not messages:
                break

            for message in messages.data:
                last_id = message.id

                if message.assistant_id and message.assistant_id.strip() not in agent_names:
                    agent = await client.beta.assistants.retrieve(message.assistant_id)
                    if agent.name and agent.name.strip():
                        agent_names[agent.id] = agent.name

                assistant_name = agent_names.get(message.assistant_id or "", None) or message.assistant_id or message.id
                content = generate_message_content(str(assistant_name), message)

                if len(content.items) > 0:
                    yield content

            if not messages.has_more:
                break

    @classmethod
    async def _retrieve_message(
        cls: type[_T], agent: "OpenAIAssistantAgent", thread_id: str, message_id: str
    ) -> "Message | None":
        """Retrieve a message from a thread."""
        message: "Message | None" = None
        count = 0
        max_retries = 3
        while count < max_retries:
            try:
                message = await agent.client.beta.threads.messages.retrieve(thread_id=thread_id, message_id=message_id)
                break
            except Exception as ex:
                logger.error(f"Failed to retrieve message {message_id} from thread {thread_id}: {ex}")
                count += 1
                if count >= max_retries:
                    logger.error(
                        f"Max retries reached. Unable to retrieve message {message_id} from thread {thread_id}."
                    )
                    break
                backoff_time: float = agent.polling_options.message_synchronization_delay.total_seconds() * (2**count)
                await asyncio.sleep(backoff_time)
        return message

    @classmethod
    async def _invoke_function_calls(
        cls: type[_T],
        kernel: "Kernel",
        fccs: list["FunctionCallContent"],
        chat_history: "ChatHistory",
        arguments: KernelArguments,
    ) -> list["AutoFunctionInvocationContext | None"]:
        """Invoke the function calls."""
        return await asyncio.gather(
            *[
                kernel.invoke_function_call(
                    function_call=function_call,
                    chat_history=chat_history,
                    arguments=arguments,
                )
                for function_call in fccs
            ],
        )

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
    async def _poll_run_status(
        cls: type[_T], agent: "OpenAIAssistantAgent", run: "Run", thread_id: str, polling_options: RunPollingOptions
    ) -> "Run":
        """Poll the run status."""
        logger.info(f"Polling run status: {run.id}, threadId: {thread_id}")

        try:
            run = await asyncio.wait_for(
                cls._poll_loop(agent, run, thread_id, polling_options),
                timeout=polling_options.run_polling_timeout.total_seconds(),
            )
        except asyncio.TimeoutError:
            timeout_duration = polling_options.run_polling_timeout
            error_message = f"Polling timed out for run id: `{run.id}` and thread id: `{thread_id}` after waiting {timeout_duration}."  # noqa: E501
            logger.error(error_message)
            raise AgentInvokeException(error_message)

        logger.info(f"Polled run status: {run.status}, {run.id}, threadId: {thread_id}")
        return run

    @classmethod
    async def _poll_loop(
        cls: type[_T], agent: "OpenAIAssistantAgent", run: "Run", thread_id: str, polling_options: RunPollingOptions
    ) -> "Run":
        """Internal polling loop."""
        count = 0
        while True:
            await asyncio.sleep(polling_options.get_polling_interval(count).total_seconds())
            count += 1

            try:
                run = await agent.client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            except Exception as e:
                logging.warning(f"Failed to retrieve run for run id: `{run.id}` and thread id: `{thread_id}`: {e}")
                # Retry anyway

            if run.status not in cls.polling_status:
                break

        return run

    @classmethod
    def _merge_options(
        cls: type[_T],
        *,
        agent: "OpenAIAssistantAgent",
        model: str | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Merge run-time options with the agent-level options.

        Run-level parameters take precedence.
        """
        return {
            "model": model if model is not None else agent.definition.model,
            "response_format": response_format if response_format is not None else None,
            "temperature": temperature if temperature is not None else agent.definition.temperature,
            "top_p": top_p if top_p is not None else agent.definition.top_p,
            "metadata": metadata if metadata is not None else agent.definition.metadata,
            **kwargs,
        }

    @classmethod
    def _generate_options(cls: type[_T], **kwargs: Any) -> dict[str, Any]:
        """Generate a dictionary of options that can be passed directly to create_run."""
        merged = cls._merge_options(**kwargs)
        agent = kwargs.get("agent")
        trunc_count = merged.get("truncation_message_count", None)
        max_completion_tokens = merged.get("max_completion_tokens", None)
        max_prompt_tokens = merged.get("max_prompt_tokens", None)
        parallel_tool_calls = merged.get("parallel_tool_calls_enabled", None)
        additional_messages = cls._translate_additional_messages(agent, merged.get("additional_messages", None))
        return {
            "model": merged.get("model"),
            "top_p": merged.get("top_p"),
            "response_format": merged.get("response_format"),
            "temperature": merged.get("temperature"),
            "truncation_strategy": trunc_count,
            "metadata": merged.get("metadata"),
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "parallel_tool_calls": parallel_tool_calls,
            "additional_messages": additional_messages,
        }

    @classmethod
    def _translate_additional_messages(
        cls: type[_T], agent, messages: "list[ChatMessageContent] | None"
    ) -> list[AdditionalMessage] | None:
        """Translate additional messages to the required format."""
        if not messages:
            return None
        return cls._form_additional_messages(messages)

    @classmethod
    def _form_additional_messages(
        cls: type[_T], messages: list["ChatMessageContent"]
    ) -> list[AdditionalMessage] | None:
        """Form the additional messages for the specified thread."""
        if not messages:
            return None

        additional_messages = []
        for message in messages:
            if not message.content:
                continue

            message_with_all: AdditionalMessage = {
                "content": message.content,
                "role": "assistant" if message.role == AuthorRole.ASSISTANT else "user",
                "attachments": cls._get_attachments(message) if message.items else None,
                "metadata": cls._get_metadata(message) if message.metadata else None,
            }
            additional_messages.append(message_with_all)
        return additional_messages

    @classmethod
    def _get_attachments(cls: type[_T], message: "ChatMessageContent") -> list[AdditionalMessageAttachment]:
        return [
            AdditionalMessageAttachment(
                file_id=file_content.file_id,
                tools=list(cls._get_tool_definition(file_content.tools)),  # type: ignore
                data_source=file_content.data_source if file_content.data_source else None,
            )
            for file_content in message.items
            if isinstance(file_content, (FileReferenceContent, StreamingFileReferenceContent))
            and file_content.file_id is not None
        ]

    @classmethod
    def _get_metadata(cls: type[_T], message: "ChatMessageContent") -> dict[str, str]:
        """Get the metadata for an agent message."""
        return {k: str(v) if v is not None else "" for k, v in (message.metadata or {}).items()}

    @classmethod
    def _get_tool_definition(cls: type[_T], tools: list[Any]) -> Iterable["AdditionalMessageAttachmentTool"]:
        if not tools:
            return
        for tool in tools:
            if tool_definition := cls.tool_metadata.get(tool):
                yield from tool_definition

    @classmethod
    def _get_tools(cls: type[_T], agent: "OpenAIAssistantAgent", kernel: "Kernel") -> list[dict[str, str]]:
        """Get the list of tools for the assistant.

        Returns:
            The list of tools.
        """
        tools: list[Any] = []

        for tool in agent.definition.tools:
            if isinstance(tool, CodeInterpreterTool):
                tools.append({"type": "code_interpreter"})
            elif isinstance(tool, FileSearchTool):
                tools.append({"type": "file_search"})

        funcs = agent.kernel.get_full_list_of_function_metadata()
        tools.extend([kernel_function_metadata_to_function_call_format(f) for f in funcs])

        return tools
