# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar, cast

from azure.ai.agents.models import (
    AgentsNamedToolChoiceType,
    AgentStreamEvent,
    AsyncAgentEventHandler,
    AsyncAgentRunStream,
    BaseAsyncAgentEventHandler,
    FunctionToolDefinition,
    ResponseFormatJsonSchemaType,
    RunStep,
    RunStepAzureAISearchToolCall,
    RunStepBingGroundingToolCall,
    RunStepCodeInterpreterToolCall,
    RunStepDeltaChunk,
    RunStepDeltaToolCallObject,
    RunStepFileSearchToolCall,
    RunStepMessageCreationDetails,
    RunStepOpenAPIToolCall,
    RunStepToolCallDetails,
    RunStepType,
    SubmitToolOutputsAction,
    ThreadMessage,
    ThreadRun,
    ToolDefinition,
    TruncationObject,
)
from azure.ai.agents.models._enums import MessageRole

from semantic_kernel.agents.azure_ai.agent_content_generation import (
    generate_azure_ai_search_content,
    generate_bing_grounding_content,
    generate_code_interpreter_content,
    generate_file_search_content,
    generate_function_call_content,
    generate_function_call_streaming_content,
    generate_function_result_content,
    generate_message_content,
    generate_openapi_content,
    generate_streaming_azure_ai_search_content,
    generate_streaming_bing_grounding_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_file_search_content,
    generate_streaming_message_content,
    generate_streaming_openapi_content,
    get_function_call_contents,
)
from semantic_kernel.agents.azure_ai.azure_ai_agent_utils import AzureAIAgentUtils
from semantic_kernel.agents.open_ai.assistant_content_generation import merge_streaming_function_results
from semantic_kernel.agents.open_ai.function_action_result import FunctionActionResult
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from azure.ai.projects.aio import AIProjectClient

    from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
        AutoFunctionInvocationContext,
    )
    from semantic_kernel.kernel import Kernel

_T = TypeVar("_T", bound="AgentThreadActions")

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AgentThreadActions:
    """AzureAI Agent Thread Actions."""

    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "cancelled", "expired", "incomplete"]

    # region Invocation Methods

    @classmethod
    async def invoke(
        cls: type[_T],
        *,
        agent: "AzureAIAgent",
        thread_id: str,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        model: str | None = None,
        instructions_override: str | None = None,
        additional_instructions: str | None = None,
        additional_messages: "list[ChatMessageContent] | None" = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        truncation_strategy: TruncationObject | None = None,
        response_format: ResponseFormatJsonSchemaType | None = None,
        parallel_tool_calls: bool | None = None,
        metadata: dict[str, str] | None = None,
        polling_options: RunPollingOptions | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the message in the thread.

        Args:
            agent: The agent to invoke.
            thread_id: The thread id.
            arguments: The kernel arguments.
            kernel: The kernel.
            model: The model.
            instructions_override: The instructions override.
            additional_instructions: The additional instructions.
            additional_messages: The additional messages to add to the thread. Only supports messages with
                role = User or Assistant.
                https://platform.openai.com/docs/api-reference/runs/createRun#runs-createrun-additional_messages
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            max_prompt_tokens: The max prompt tokens.
            max_completion_tokens: The max completion tokens.
            truncation_strategy: The truncation strategy.
            response_format: The response format.
            parallel_tool_calls: The parallel tool calls.
            metadata: The metadata.
            polling_options: The polling options defined at the run-level. These will override the agent-level
                polling options.
            kwargs: Additional keyword arguments.

        Returns:
            A tuple of the visibility flag and the invoked message.
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

        run_options = cls._generate_options(
            agent=agent,
            model=model,
            additional_messages=additional_messages,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            truncation_strategy=truncation_strategy,
            response_format=response_format,
            parallel_tool_calls=parallel_tool_calls,
        )
        # Remove keys with None values.
        run_options = {k: v for k, v in run_options.items() if v is not None}

        run: ThreadRun = await agent.client.agents.runs.create(
            agent_id=agent.id,
            thread_id=thread_id,
            instructions=merged_instructions or agent.instructions,
            tools=tools,
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
                raise AgentInvokeException(
                    f"Run failed with status: `{run.status}` for agent `{agent.name}` and thread `{thread_id}` "
                    f"with error: {error_message}"
                )

            # Check if function calling is required
            if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
                logger.debug(f"Run [{run.id}] requires tool action for agent `{agent.name}` and thread `{thread_id}`")
                fccs = get_function_call_contents(run, function_steps)
                if fccs:
                    logger.debug(
                        f"Yielding generate_function_call_content for agent `{agent.name}` and "
                        f"thread `{thread_id}`, visibility False"
                    )
                    yield False, generate_function_call_content(agent_name=agent.name, fccs=fccs)

                    from semantic_kernel.contents.chat_history import ChatHistory

                    chat_history = ChatHistory() if kwargs.get("chat_history") is None else kwargs["chat_history"]
                    _ = await cls._invoke_function_calls(
                        kernel=kernel, fccs=fccs, chat_history=chat_history, arguments=arguments
                    )

                    tool_outputs = cls._format_tool_outputs(fccs, chat_history)
                    await agent.client.agents.runs.submit_tool_outputs(
                        run_id=run.id,
                        thread_id=thread_id,
                        tool_outputs=tool_outputs,  # type: ignore
                    )
                    logger.debug(f"Submitted tool outputs for agent `{agent.name}` and thread `{thread_id}`")
                    continue

            steps: list[RunStep] = []
            async for steps_response in agent.client.agents.run_steps.list(thread_id=thread_id, run_id=run.id):
                steps.append(steps_response)
            logger.debug(f"Call for steps_response for run [{run.id}] agent `{agent.name}` and thread `{thread_id}`")

            def sort_key(step: RunStep):
                # Put tool_calls first, then message_creation.
                # If multiple steps share a type, break ties by completed_at.
                return (0 if step.type == "tool_calls" else 1, step.completed_at)

            completed_steps_to_process = sorted(
                [s for s in steps if s.completed_at is not None and s.id not in processed_step_ids],
                key=sort_key,
            )

            logger.debug(
                f"Completed steps to process for run [{run.id}] agent `{agent.name}` and thread `{thread_id}` "
                f"with length `{len(completed_steps_to_process)}`"
            )

            message_count = 0
            for completed_step in completed_steps_to_process:
                match completed_step.type:
                    case RunStepType.TOOL_CALLS:
                        logger.debug(
                            f"Entering step type tool_calls for run [{run.id}], agent `{agent.name}` and "
                            f"thread `{thread_id}`"
                        )
                        tool_call_details: RunStepToolCallDetails = cast(
                            RunStepToolCallDetails, completed_step.step_details
                        )
                        for tool_call in tool_call_details.tool_calls:
                            is_visible = False
                            content: "ChatMessageContent | None" = None
                            match tool_call.type:
                                case AgentsNamedToolChoiceType.CODE_INTERPRETER:
                                    logger.debug(
                                        f"Entering tool_calls (code_interpreter) for run [{run.id}], agent "
                                        f"`{agent.name}` and thread `{thread_id}`"
                                    )
                                    code_call: RunStepCodeInterpreterToolCall = cast(
                                        RunStepCodeInterpreterToolCall, tool_call
                                    )
                                    content = generate_code_interpreter_content(
                                        agent.name,
                                        code_call.code_interpreter.input,
                                    )
                                    is_visible = True
                                case AgentsNamedToolChoiceType.FUNCTION:
                                    logger.debug(
                                        f"Entering tool_calls (function) for run [{run.id}], agent `{agent.name}` "
                                        f"and thread `{thread_id}`"
                                    )
                                    function_step = function_steps.get(tool_call.id)
                                    assert function_step is not None  # nosec
                                    content = generate_function_result_content(
                                        agent_name=agent.name,
                                        function_step=function_step,
                                        tool_call=tool_call,  # type: ignore
                                    )
                                case (
                                    AgentsNamedToolChoiceType.BING_GROUNDING
                                    | AgentsNamedToolChoiceType.BING_CUSTOM_SEARCH
                                ):
                                    logger.debug(
                                        f"Entering tool_calls (bing_grounding) for run [{run.id}], agent "
                                        f" `{agent.name}` and thread `{thread_id}`"
                                    )
                                    bing_call: RunStepBingGroundingToolCall = cast(
                                        RunStepBingGroundingToolCall, tool_call
                                    )
                                    content = generate_bing_grounding_content(
                                        agent_name=agent.name, bing_tool_call=bing_call
                                    )
                                case AgentsNamedToolChoiceType.AZURE_AI_SEARCH:
                                    logger.debug(
                                        f"Entering tool_calls (azure_ai_search) for run [{run.id}], agent "
                                        f" `{agent.name}` and thread `{thread_id}`"
                                    )
                                    azure_ai_search_call: RunStepAzureAISearchToolCall = cast(
                                        RunStepAzureAISearchToolCall, tool_call
                                    )
                                    content = generate_azure_ai_search_content(
                                        agent_name=agent.name, azure_ai_search_tool_call=azure_ai_search_call
                                    )
                                case AgentsNamedToolChoiceType.FILE_SEARCH:
                                    logger.debug(
                                        f"Entering tool_calls (file_search) for run [{run.id}], agent "
                                        f" `{agent.name}` and thread `{thread_id}`"
                                    )
                                    file_search_call: RunStepFileSearchToolCall = cast(
                                        RunStepFileSearchToolCall, tool_call
                                    )
                                    content = generate_file_search_content(
                                        agent_name=agent.name, file_search_tool_call=file_search_call
                                    )
                                case "openapi":
                                    logger.debug(
                                        f"Entering tool_calls (openapi) for run [{run.id}], agent "
                                        f" `{agent.name}` and thread `{thread_id}`"
                                    )
                                    openapi_tool_call: RunStepOpenAPIToolCall = cast(RunStepOpenAPIToolCall, tool_call)
                                    content = generate_openapi_content(
                                        agent_name=agent.name,
                                        openapi_tool_call=openapi_tool_call,
                                    )

                            if content:
                                message_count += 1
                                logger.debug(
                                    f"Yielding tool_message for run [{run.id}], agent `{agent.name}`, "
                                    f"thread `{thread_id}`, message count `{message_count}`, "
                                    f"is_visible `{is_visible}`"
                                )
                                yield is_visible, content
                    case RunStepType.MESSAGE_CREATION:
                        logger.debug(
                            f"Entering message_creation for run [{run.id}], agent `{agent.name}` and thread "
                            f"`{thread_id}`"
                        )
                        message_call_details: RunStepMessageCreationDetails = cast(
                            RunStepMessageCreationDetails, completed_step.step_details
                        )
                        message = await cls._retrieve_message(
                            agent=agent,
                            thread_id=thread_id,
                            message_id=message_call_details.message_creation.message_id,  # type: ignore
                        )
                        if message:
                            content = generate_message_content(agent.name, message, completed_step)
                            if content and len(content.items) > 0:
                                message_count += 1
                                logger.debug(
                                    f"Yielding message_creation for run [{run.id}], agent `{agent.name}`, "
                                    f"thread `{thread_id}`, message count `{message_count}`, is_visible `True`"
                                )
                                yield True, content
                processed_step_ids.add(completed_step.id)

    @classmethod
    async def invoke_stream(
        cls: type[_T],
        *,
        agent: "AzureAIAgent",
        thread_id: str,
        additional_instructions: str | None = None,
        additional_messages: "list[ChatMessageContent] | None" = None,
        arguments: KernelArguments | None = None,
        instructions_override: str | None = None,
        kernel: "Kernel | None" = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        output_messages: list[ChatMessageContent] | None = None,
        parallel_tool_calls: bool | None = None,
        response_format: ResponseFormatJsonSchemaType | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: TruncationObject | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the agent stream and yield ChatMessageContent continuously.

        Args:
            agent: The agent to invoke.
            thread_id: The thread id.
            additional_instructions: The additional instructions.
            additional_messages: The additional messages to add to the thread. Only supports messages with
                role = User or Assistant.
                https://platform.openai.com/docs/api-reference/runs/createRun
            arguments: The kernel arguments.
            instructions_override: The instructions override.
            kernel: The kernel.
            metadata: The metadata.
            model: The model.
            max_prompt_tokens: The max prompt tokens.
            max_completion_tokens: The max completion tokens.
            output_messages: The output messages received from the agent. These are full content messages
                formed from the streamed chunks.
            parallel_tool_calls: Whether to configure parallel tool calls.
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
        arguments = agent._merge_arguments(arguments)

        tools = cls._get_tools(agent=agent, kernel=kernel)  # type: ignore

        base_instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        merged_instructions: str = ""
        if instructions_override is not None:
            merged_instructions = instructions_override
        elif base_instructions and additional_instructions:
            merged_instructions = f"{base_instructions}\n\n{additional_instructions}"
        else:
            merged_instructions = base_instructions or additional_instructions or ""

        run_options = cls._generate_options(
            agent=agent,
            model=model,
            additional_messages=additional_messages,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            truncation_strategy=truncation_strategy,
            response_format=response_format,
            parallel_tool_calls=parallel_tool_calls,
        )
        run_options = {k: v for k, v in run_options.items() if v is not None}

        stream: AsyncAgentRunStream = await agent.client.agents.runs.stream(
            agent_id=agent.id,
            thread_id=thread_id,
            instructions=merged_instructions or agent.instructions,
            tools=tools,
            **run_options,
        )

        function_steps: dict[str, FunctionCallContent] = {}
        active_messages: dict[str, RunStep] = {}

        async for content in cls._process_stream_events(
            stream=stream,
            agent=agent,
            thread_id=thread_id,
            output_messages=output_messages,
            kernel=kernel,
            arguments=arguments,
            function_steps=function_steps,
            active_messages=active_messages,
        ):
            if content:
                yield content

    @classmethod
    async def _process_stream_events(
        cls: type[_T],
        stream: AsyncAgentRunStream,
        agent: "AzureAIAgent",
        thread_id: str,
        kernel: "Kernel",
        arguments: KernelArguments,
        function_steps: dict[str, FunctionCallContent],
        active_messages: dict[str, RunStep],
        output_messages: "list[ChatMessageContent] | None" = None,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Process events from the main stream and delegate tool output handling as needed."""
        while True:
            # Use 'async with' only if the stream supports async context management (main agent stream).
            # Tool output handlers only support async iteration, not context management.
            if hasattr(stream, "__aenter__") and hasattr(stream, "__aexit__"):
                async with stream as response_stream:
                    stream_iter = response_stream
            else:
                stream_iter = stream
            async for event_type, event_data, _ in stream_iter:
                if event_type == AgentStreamEvent.THREAD_RUN_CREATED:
                    run = event_data
                    logger.info(f"Assistant run created with ID: {run.id}")

                elif event_type == AgentStreamEvent.THREAD_RUN_IN_PROGRESS:
                    run_step = cast(RunStep, event_data)
                    logger.info(f"Assistant run in progress with ID: {run_step.id}")

                elif event_type == AgentStreamEvent.THREAD_MESSAGE_DELTA:
                    yield generate_streaming_message_content(agent.name, event_data)

                elif event_type == AgentStreamEvent.THREAD_RUN_STEP_COMPLETED:
                    step_completed = cast(RunStep, event_data)
                    logger.info(f"Run step completed with ID: {step_completed.id}")
                    if isinstance(step_completed.step_details, RunStepMessageCreationDetails):
                        msg_id = step_completed.step_details.message_creation.message_id
                        active_messages.setdefault(msg_id, step_completed)

                elif event_type == AgentStreamEvent.THREAD_RUN_STEP_DELTA:
                    run_step_event: RunStepDeltaChunk = event_data
                    details = run_step_event.delta.step_details
                    if not details:
                        continue
                    if isinstance(details, RunStepDeltaToolCallObject) and details.tool_calls:
                        content_is_visible = False
                        for tool_call in details.tool_calls:
                            logger.debug(
                                f"Generating content for tool call type `{tool_call.type}`, agent `{agent.name}` and "
                                f"thread `{thread_id}` with tool call details: {details}"
                            )
                            content = None
                            match tool_call.type:
                                # Function Calling-related content is emitted as a single message
                                # via the `on_intermediate_message` callback.
                                case AgentsNamedToolChoiceType.CODE_INTERPRETER:
                                    content = generate_streaming_code_interpreter_content(agent.name, details)
                                    content_is_visible = True
                                case (
                                    AgentsNamedToolChoiceType.BING_GROUNDING
                                    | AgentsNamedToolChoiceType.BING_CUSTOM_SEARCH
                                ):
                                    content = generate_streaming_bing_grounding_content(
                                        agent_name=agent.name, step_details=details
                                    )
                                case AgentsNamedToolChoiceType.AZURE_AI_SEARCH:
                                    content = generate_streaming_azure_ai_search_content(
                                        agent_name=agent.name, step_details=details
                                    )
                                case AgentsNamedToolChoiceType.FILE_SEARCH:
                                    content = generate_streaming_file_search_content(
                                        agent_name=agent.name, step_details=details
                                    )
                                case "openapi":
                                    # There's no enum for OpenAPI tool calls as part of `AgentsNamedToolChoiceType`
                                    # so we handle it separately.
                                    content = generate_streaming_openapi_content(
                                        agent_name=agent.name, step_details=details
                                    )
                            if content:
                                if output_messages is not None:
                                    output_messages.append(content)
                                if content_is_visible:
                                    yield content

                elif event_type == AgentStreamEvent.THREAD_RUN_REQUIRES_ACTION:
                    logger.debug(
                        f"Entering step type {event_type}, agent `{agent.name}` and "
                        f"thread `{thread_id}` with event data: {event_data}"
                    )
                    run = cast(ThreadRun, event_data)
                    action_result = await cls._handle_streaming_requires_action(
                        agent_name=agent.name,
                        kernel=kernel,
                        run=run,
                        function_steps=function_steps,
                        arguments=arguments,
                    )
                    if action_result is None:
                        raise RuntimeError(
                            f"Function call required but no function steps found for agent `{agent.name}` "
                            f"thread: {thread_id}."
                        )

                    for content in (
                        action_result.function_call_streaming_content,
                        action_result.function_result_streaming_content,
                    ):
                        if content and output_messages is not None:
                            output_messages.append(content)

                    handler: BaseAsyncAgentEventHandler = AsyncAgentEventHandler()
                    await agent.client.agents.runs.submit_tool_outputs_stream(
                        run_id=run.id,
                        thread_id=thread_id,
                        tool_outputs=action_result.tool_outputs,  # type: ignore
                        event_handler=handler,
                    )
                    # Pass the handler to the stream to continue processing
                    stream = handler  # type: ignore

                    logger.debug(
                        f"Submitted tool outputs stream for agent `{agent.name}` and "
                        f"thread `{thread_id}` and run id `{run.id}`"
                    )
                    break

                elif event_type == AgentStreamEvent.THREAD_RUN_COMPLETED:
                    logger.debug(
                        f"Entering step type {event_type}, agent `{agent.name}` and "
                        f"thread `{thread_id}` and run id `{run.id}`"
                    )
                    run = cast(ThreadRun, event_data)
                    logger.info(f"Run completed with ID: {run.id}")
                    if active_messages:
                        for msg_id, step in active_messages.items():
                            message = await cls._retrieve_message(agent=agent, thread_id=thread_id, message_id=msg_id)
                            if message and hasattr(message, "content"):
                                final_content = generate_message_content(agent.name, message, step)
                                if output_messages is not None:
                                    output_messages.append(final_content)
                    return

                elif event_type == AgentStreamEvent.THREAD_RUN_FAILED:
                    run_failed = cast(ThreadRun, event_data)
                    error_message = (
                        run_failed.last_error.message if run_failed.last_error and run_failed.last_error.message else ""
                    )
                    raise RuntimeError(
                        f"Run failed with status: `{run_failed.status}` for agent `{agent.name}` "
                        f"thread `{thread_id}` with error: {error_message}"
                    )
            else:
                break
        return

    # endregion

    # region Messaging Handling Methods

    @classmethod
    async def create_thread(
        cls: type[_T],
        client: "AIProjectClient",
        **kwargs: Any,
    ) -> str:
        """Create a thread.

        Args:
            client: The client to use to create the thread.
            kwargs: Additional keyword arguments.

        Returns:
            The ID of the created thread.
        """
        thread = await client.agents.threads.create(**kwargs)
        return thread.id

    @classmethod
    async def create_message(
        cls: type[_T],
        client: "AIProjectClient",
        thread_id: str,
        message: "str | ChatMessageContent",
        **kwargs: Any,
    ) -> "ThreadMessage | None":
        """Create a message in the thread.

        Args:
            client: The client to use to create the message.
            thread_id: The ID of the thread to create the message in.
            message: The message to create.
            kwargs: Additional keyword arguments.

        Returns:
            The created message.
        """
        if isinstance(message, str):
            message = ChatMessageContent(role=AuthorRole.USER, content=message)

        if any(isinstance(item, FunctionCallContent) for item in message.items):
            return None

        if not message.content.strip():
            return None

        return await client.agents.messages.create(
            thread_id=thread_id,
            role=MessageRole.USER if message.role == AuthorRole.USER else MessageRole.AGENT,
            content=message.content,
            attachments=AzureAIAgentUtils.get_attachments(message),
            metadata=AzureAIAgentUtils.get_metadata(message),
            **kwargs,
        )

    @classmethod
    async def get_messages(
        cls: type[_T],
        client: "AIProjectClient",
        thread_id: str,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> AsyncIterable["ChatMessageContent"]:
        """Get messages from a thread.

        Args:
            client: The client to use to get the messages.
            thread_id: The ID of the thread to get the messages from.
            sort_order: The order to sort the messages in.

        Yields:
            An AsyncIterable of ChatMessageContent that includes the thread messages.
        """
        agent_names: dict[str, str] = {}

        async for message in client.agents.messages.list(
            thread_id=thread_id,
            run_id=None,
            limit=None,
            order=sort_order,
            before=None,
        ):
            assistant_name: str | None = None

            if message.agent_id and message.agent_id.strip() and message.agent_id not in agent_names:
                agent = await client.agents.get_agent(message.agent_id)
                if agent.name and agent.name.strip():
                    agent_names[agent.id] = agent.name

            assistant_name = agent_names.get(message.agent_id) or message.agent_id

            content = generate_message_content(assistant_name, message)

            if len(content.items) > 0:
                yield content

    # endregion

    # region Internal Methods

    @classmethod
    def _merge_options(
        cls: type[_T],
        *,
        agent: "AzureAIAgent",
        model: str | None = None,
        response_format: ResponseFormatJsonSchemaType | None = None,
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
            "response_format": response_format if response_format is not None else agent.definition.response_format,
            "temperature": temperature if temperature is not None else agent.definition.temperature,
            "top_p": top_p if top_p is not None else agent.definition.top_p,
            "metadata": metadata if metadata is not None else agent.definition.metadata,
            **kwargs,
        }

    @classmethod
    def _generate_options(cls: type[_T], **kwargs: Any) -> dict[str, Any]:
        """Generate a dictionary of options that can be passed directly to create_run."""
        merged = cls._merge_options(**kwargs)
        truncation_strategy = merged.get("truncation_strategy", None)
        max_completion_tokens = merged.get("max_completion_tokens", None)
        max_prompt_tokens = merged.get("max_prompt_tokens", None)
        parallel_tool_calls = merged.get("parallel_tool_calls_enabled", None)
        additional_messages = cls._translate_additional_messages(merged.get("additional_messages", None))
        return {
            "model": merged.get("model"),
            "top_p": merged.get("top_p"),
            "response_format": merged.get("response_format"),
            "temperature": merged.get("temperature"),
            "truncation_strategy": truncation_strategy,
            "metadata": merged.get("metadata"),
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "parallel_tool_calls": parallel_tool_calls,
            "additional_messages": additional_messages,
        }

    @classmethod
    def _translate_additional_messages(
        cls: type[_T], messages: "list[ChatMessageContent] | None"
    ) -> list[ThreadMessage] | None:
        """Translate additional messages to the required format."""
        if not messages:
            return None
        return AzureAIAgentUtils.get_thread_messages(messages)

    @classmethod
    def _prepare_tool_definition(cls: type[_T], tool: dict | ToolDefinition) -> dict | ToolDefinition:
        """Prepare the tool definition."""
        if tool.get("type") == "openapi" and "openapi" in tool:
            openapi_data = dict(tool["openapi"])
            openapi_data.pop("functions", None)
            tool = dict(tool)
            tool["openapi"] = openapi_data
        return tool

    @staticmethod
    def _deduplicate_tools(existing_tools: list[dict], new_tools: list[dict]) -> list[dict]:
        existing_names = {
            tool["function"]["name"] for tool in existing_tools if "function" in tool and "name" in tool["function"]
        }
        return [tool for tool in new_tools if tool.get("function", {}).get("name") not in existing_names]

    @classmethod
    def _get_tools(cls: type[_T], agent: "AzureAIAgent", kernel: "Kernel") -> list[dict[str, Any] | ToolDefinition]:
        """Get the tools for the agent."""
        tools: list[Any] = list(agent.definition.tools)
        funcs = kernel.get_full_list_of_function_metadata()
        cls._validate_function_tools_registered(tools, funcs)
        dict_defs = [kernel_function_metadata_to_function_call_format(f) for f in funcs]
        deduped_defs = cls._deduplicate_tools(tools, dict_defs)
        tools.extend(deduped_defs)
        return [cls._prepare_tool_definition(tool) for tool in tools]

    @staticmethod
    def _validate_function_tools_registered(
        tools: list[Any],
        funcs: list[Any],
    ) -> None:
        """Validate that all function tools are registered with the kernel."""
        function_tool_names = set()
        for tool in tools:
            if isinstance(tool, FunctionToolDefinition):
                agent_tool_func_name = getattr(tool.function, "name", None)
                if agent_tool_func_name:
                    function_tool_names.add(agent_tool_func_name)

        kernel_function_names = set()
        for f in funcs:
            kernel_func_name = (
                f.fully_qualified_name
                if isinstance(f, KernelFunctionMetadata)
                else getattr(f, "full_qualified_name", None)
            )
            if kernel_func_name:
                kernel_function_names.add(kernel_func_name)

        missing_functions = function_tool_names - kernel_function_names
        if missing_functions:
            raise AgentInvokeException(
                f"The following function tool(s) are defined on the agent but missing from the kernel: "
                f"{sorted(missing_functions)}. "
                f"Please ensure all required tools are registered with the kernel."
            )

    @classmethod
    async def _poll_run_status(
        cls: type[_T], agent: "AzureAIAgent", run: ThreadRun, thread_id: str, polling_options: RunPollingOptions
    ) -> ThreadRun:
        """Poll the run status."""
        logger.info(f"Polling run status: {run.id}, threadId: {thread_id}")
        try:
            run = await asyncio.wait_for(
                cls._poll_loop(agent=agent, run=run, thread_id=thread_id, polling_options=polling_options),
                timeout=polling_options.run_polling_timeout.total_seconds(),
            )
        except asyncio.TimeoutError:
            timeout_duration = polling_options.run_polling_timeout
            error_message = (
                f"Polling timed out for run id: `{run.id}` and thread id: `{thread_id}` "
                f"after waiting {timeout_duration}."
            )
            logger.error(error_message)
            raise AgentInvokeException(error_message)
        logger.info(f"Polled run status: {run.status}, {run.id}, threadId: {thread_id}")
        return run

    @classmethod
    async def _poll_loop(
        cls: type[_T], agent: "AzureAIAgent", run: ThreadRun, thread_id: str, polling_options: RunPollingOptions
    ) -> ThreadRun:
        """Continuously poll the run status until it is no longer pending."""
        count = 0
        while True:
            await asyncio.sleep(polling_options.get_polling_interval(count).total_seconds())
            count += 1
            try:
                run = await agent.client.agents.runs.get(run_id=run.id, thread_id=thread_id)
            except Exception as e:
                logger.warning(f"Failed to retrieve run for run id: `{run.id}` and thread id: `{thread_id}`: {e}")
            if run.status not in cls.polling_status:
                break
        return run

    @classmethod
    async def _retrieve_message(
        cls: type[_T], agent: "AzureAIAgent", thread_id: str, message_id: str
    ) -> ThreadMessage | None:
        """Retrieve a message from a thread."""
        message: ThreadMessage | None = None
        count = 0
        max_retries = 3
        while count < max_retries:
            try:
                message = await agent.client.agents.messages.get(thread_id=thread_id, message_id=message_id)
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
            if isinstance(tool_call, FunctionResultContent) and tool_call.id is not None
        }
        return [
            {"tool_call_id": fcc.id, "output": str(tool_call_lookup[fcc.id].result)}
            for fcc in fccs
            if fcc.id in tool_call_lookup
        ]

    @classmethod
    async def _handle_streaming_requires_action(
        cls: type[_T],
        agent_name: str,
        kernel: "Kernel",
        run: ThreadRun,
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
