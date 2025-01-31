# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar

from azure.ai.projects.models import (
    AgentStreamEvent,
    AsyncAgentRunStream,
    OpenAIPageableListOfThreadMessage,
    RunStep,
    RunStepCodeInterpreterToolCall,
    RunStepDeltaChunk,
    RunStepDeltaToolCallObject,
    RunStepMessageCreationDetails,
    RunStepToolCallDetails,
    SubmitToolOutputsAction,
    ThreadMessage,
    ThreadRun,
)
from azure.ai.projects.models._enums import MessageRole

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.agents.azure_ai.azure_ai_agent_utils import AzureAIAgentUtils
from semantic_kernel.agents.open_ai.assistant_content_generation import (
    generate_code_interpreter_content,
    generate_function_call_content,
    generate_function_result_content,
    generate_message_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_function_content,
    generate_streaming_message_content,
    get_function_call_contents,
)
from semantic_kernel.agents.open_ai.function_action_result import FunctionActionResult
from semantic_kernel.connectors.ai.function_calling_utils import (
    kernel_function_metadata_to_function_call_format,
    merge_function_results,
)
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from azure.ai.projects.aio import AIProjectClient

    from semantic_kernel.contents import ChatHistory, ChatMessageContent
    from semantic_kernel.functions import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AgentThreadActions:
    """AzureAI Agent Thread Actions."""

    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "cancelled", "expired", "incomplete"]

    # region Invocation Methods

    @classmethod
    async def invoke(
        cls,
        *,
        agent: "AzureAIAgent",
        thread_id: str,
        arguments: "KernelArguments",
        kernel: "Kernel",
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the message in the thread.

        Args:
            agent: The agent to invoke.
            thread_id: The thread id.
            arguments: The kernel arguments.
            kernel: The kernel.
            kwargs: Additional keyword arguments.

        Returns:
            The a tuple of the visibility and the invoked message.
        """
        tools = cls._get_tools(agent, kernel)

        instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        run: ThreadRun = await agent.client.agents.create_run(
            assistant_id=agent.id,
            thread_id=thread_id,
            instructions=instructions,
            tools=tools,
            **kwargs,
        )

        processed_step_ids = set()
        function_steps: dict[str, "FunctionCallContent"] = {}

        while run.status != "completed":
            run = await cls._poll_run_status(run=run, thread_id=thread_id)

            if run.status in cls.error_message_states:
                error_message = ""
                if run.last_error and run.last_error.message:
                    error_message = run.last_error.message
                raise AgentInvokeException(
                    f"Run failed with status: `{run.status}` for agent `{agent.name}` and thread `{thread_id}` "
                    f"with error: {error_message}"
                )

            # Check if function calling required
            if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
                logger.debug(f"Run [{run.id}] requires tool action for agent `{agent.name}` and thread `{thread_id}`")
                fccs = get_function_call_contents(run, function_steps)
                if fccs:
                    logger.debug(
                        f"Yielding `generate_function_call_content` for agent `{agent.name}` and "
                        f"thread `{thread_id}`, visibility False"
                    )
                    yield False, generate_function_call_content(agent_name=agent.name, fccs=fccs)

                    from semantic_kernel.contents.chat_history import ChatHistory

                    chat_history = ChatHistory()
                    _ = await cls._invoke_function_calls(fccs=fccs, chat_history=chat_history)

                    tool_outputs = cls._format_tool_outputs(fccs, chat_history)
                    await agent.client.agents.submit_tool_outputs_to_run(
                        run_id=run.id,
                        thread_id=thread_id,
                        tool_outputs=tool_outputs,  # type: ignore
                    )
                    logger.debug(f"Submitted tool outputs for agent `{agent.name}` and thread `{thread_id}`")

            steps_response = await agent.client.agents.list_run_steps(run_id=run.id, thread_id=thread_id)
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
                    tool_call_details: RunStepToolCallDetails = completed_step.step_details
                    for tool_call in tool_call_details.tool_calls:
                        is_visible = False
                        content: "ChatMessageContent | None" = None
                        if tool_call.type == "code_interpreter":
                            logger.debug(
                                f"Entering step type tool_calls for run [{run.id}], [code_interpreter] for "
                                f"agent `{agent.name}` and thread `{thread_id}`"
                            )
                            code_call: RunStepCodeInterpreterToolCall = tool_call
                            content = generate_code_interpreter_content(
                                agent.name,
                                code_call.code_interpreter.input,
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
                    message_call_details: RunStepMessageCreationDetails = completed_step.step_details
                    message = await cls._retrieve_message(
                        thread_id=thread_id,
                        message_id=message_call_details.message_creation.message_id,  # type: ignore
                    )
                    if message:
                        content = generate_message_content(agent.name, message)
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
        cls,
        *,
        agent: "AzureAIAgent",
        thread_id: str,
        messages: list["ChatMessageContent"],
        arguments: "KernelArguments",
        kernel: "Kernel",
        **kwargs: Any,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent stream."""
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or agent.kernel
        arguments = agent.merge_arguments(arguments)

        tools = cls._get_tools()

        # Get base instructions from the prompt template, if any
        instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        stream: AsyncAgentRunStream = agent.client.agents.create_stream(
            assistant_id=agent.id,
            thread_id=thread_id,
            instructions=instructions,
            tools=tools,  # type: ignore
        )

        function_steps: dict[str, "FunctionCallContent"] = {}
        active_messages: dict[str, RunStep] = {}

        while True:
            async with stream as response_stream:
                async for event_type, event_data, _ in response_stream:
                    match event_type:
                        case AgentStreamEvent.THREAD_RUN_CREATED:
                            run: ThreadRun = event_data
                            logger.info(f"Assistant run created with ID: {run.id}")
                        case AgentStreamEvent.THREAD_RUN_IN_PROGRESS:
                            run: RunStep = event_data
                            logger.info(f"Assistant run in progress with ID: {run.id}")
                        case AgentStreamEvent.THREAD_MESSAGE_DELTA:
                            content = generate_streaming_message_content(agent.name, event_data)
                            yield content
                        case AgentStreamEvent.THREAD_RUN_STEP_COMPLETED:
                            step_completed: RunStep = event_data
                            logger.info(f"Run step completed with ID: {step_completed.id}")
                            if isinstance(step_completed.step_details, RunStepMessageCreationDetails):
                                message_id = step_completed.step_details.message_creation.message_id
                                if message_id not in active_messages:
                                    active_messages[message_id] = event_data
                        case AgentStreamEvent.THREAD_RUN_STEP_DELTA:
                            run_step_event_data: RunStepDeltaChunk = event_data
                            run_step_details = run_step_event_data.delta.step_details
                            if isinstance(run_step_details, RunStepDeltaToolCallObject):
                                for tool_call in run_step_details.tool_calls:
                                    tool_content = None
                                    if tool_call.type == "function":
                                        tool_content = generate_streaming_function_content(agent.name, run_step_details)
                                    elif tool_call.type == "code_interpreter":
                                        tool_content = generate_streaming_code_interpreter_content(
                                            agent.name, run_step_details
                                        )
                                    if tool_content:
                                        yield tool_content
                        case AgentStreamEvent.THREAD_RUN_REQUIRES_ACTION:
                            run: ThreadRun = event_data
                            function_action_result = await cls._handle_streaming_requires_action(
                                agent, run, function_steps
                            )
                            if function_action_result is None:
                                raise AgentInvokeException(
                                    f"Function call required but no function steps found for agent `{agent.name}` "
                                    f"thread: {thread_id}."
                                )
                            if function_action_result.function_result_content:
                                # Yield the function result content to the caller
                                yield function_action_result.function_result_content
                                if messages is not None:
                                    # Add the function result content to the messages list, if it exists
                                    messages.append(function_action_result.function_result_content)
                            if function_action_result.function_call_content:
                                if messages is not None:
                                    messages.append(function_action_result.function_call_content)
                                stream = agent.client.agents.submit_tool_outputs_to_stream(
                                    run_id=run.id,
                                    thread_id=thread_id,
                                    tool_outputs=function_action_result.tool_outputs,  # type: ignore
                                )
                                break
                        case AgentStreamEvent.THREAD_RUN_COMPLETED:
                            run: ThreadRun = event_data
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
                                        content = generate_message_content(agent.name, message, step)
                                        if messages is not None:
                                            messages.append(content)
                            return
                        case AgentStreamEvent.THREAD_RUN_FAILED:
                            run = event_data  # type: ignore
                            error_message = ""
                            if run.last_error and run.last_error.message:
                                error_message = run.last_error.message
                            raise AgentInvokeException(
                                f"Run failed with status: `{run.status}` for agent `{agent.name}` and "
                                f"thread `{thread_id}` "
                                f"with error: {error_message}"
                            )
                else:
                    # If the inner loop completes without encountering a 'break', exit the outer loop
                    break

    # endregion

    # region Messaging Handling Methods

    @classmethod
    async def create_thread(
        cls,
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
        thread = await client.agents.create_thread(**kwargs)
        return thread.id

    @classmethod
    async def create_message(
        cls, client: "AIProjectClient", thread_id: str, message: "ChatMessageContent", **kwargs: Any
    ) -> None:
        """Create a message in the thread.

        Args:
            client: The client to use to create the message.
            thread_id: The ID of the thread to create the message in.
            message: The message to create.
            kwargs: Additional keyword arguments.
        """
        if any(isinstance(item, FunctionCallContent) for item in message.items):
            return

        if not message.content.strip():
            return

        message = await client.agents.create_message(
            thread_id=thread_id,
            role=MessageRole.USER if message.role == AuthorRole.USER else MessageRole.AGENT,
            content=message.content,
            attachments=AzureAIAgentUtils.get_attachments(message),
            metadata=AzureAIAgentUtils.get_metadata(message),
            **kwargs,
        )

    @classmethod
    async def get_messages(
        cls,
        client: AIProjectClient,
        thread_id: str,
    ) -> AsyncIterable[ChatMessageContent]:
        """Get messages from a thread."""
        agent_names: dict[str, Any] = {}
        last_id: str | None = None
        messages: OpenAIPageableListOfThreadMessage = None

        while True:
            messages = await client.agents.list_messages(
                thread_id=thread_id,
                run_id=None,
                limit=None,
                sort_order="desc",
                after=last_id,
                before=None,
            )

            if not messages:
                break

            for message in messages.data:
                print(message.id)
                last_id = message.id
                assistant_name: str | None = None

                if message.assistant_id and message.assistant_id.strip() and message.assistant_id not in agent_names:
                    assistant = await client.agents.get_agent(
                        message.assistant_id,
                    )
                    if assistant.name and assistant.name.strip():
                        agent_names[assistant.id] = assistant.name

                # Fallback to message.assistant_id if no name is found
                assistant_name = agent_names.get(message.assistant_id) or message.assistant_id

                # Build chat content
                content: ChatMessageContent = generate_message_content(assistant_name, message)

                # Only yield if there are actual items in the content
                if len(content.items) > 0:
                    yield content

            # Check if there are more messages to fetch
            if not messages.has_more:
                break

    # endregion

    # region Internal Methods

    @classmethod
    def _get_tools(cls, agent: "AzureAIAgent", kernel: "Kernel") -> list[dict[str, str]]:
        """Get the list of tools for the agent.

        Returns:
            The list of tools.
        """
        tools = []

        tools.extend(agent.tools)

        funcs = kernel.get_full_list_of_function_metadata()
        tools.extend([kernel_function_metadata_to_function_call_format(f) for f in funcs])

        return tools

    @classmethod
    async def _poll_run_status(cls, agent: "AzureAIAgent", run: ThreadRun, thread_id: str) -> ThreadRun:
        """Poll the run status."""
        logger.info(f"Polling run status: {run.id}, threadId: {thread_id}")

        count = 0
        try:
            run = await asyncio.wait_for(
                cls._poll_loop(run, thread_id, count), timeout=agent.polling_options.run_polling_timeout.total_seconds()
            )
        except asyncio.TimeoutError:
            timeout_duration = agent.polling_options.run_polling_timeout
            error_message = f"Polling timed out for run id: `{run.id}` and thread id: `{thread_id}` after waiting {timeout_duration}."  # noqa: E501
            logger.error(error_message)
            raise AgentInvokeException(error_message)

        logger.info(f"Polled run status: {run.status}, {run.id}, threadId: {thread_id}")
        return run

    @classmethod
    async def _poll_loop(cls, agent: "AzureAIAgent", run: ThreadRun, thread_id: str, count: int) -> ThreadRun:
        """Internal polling loop."""
        while True:
            await asyncio.sleep(agent.polling_options.get_polling_interval(count).total_seconds())
            count += 1

            try:
                run = await agent.client.agents.get_run(run_id=run.id, thread_id=thread_id)
            except Exception as e:
                logging.warning(f"Failed to retrieve run for run id: `{run.id}` and thread id: `{thread_id}`: {e}")
                # Retry anyway

            if run.status not in cls.polling_status:
                break

        return run

    @classmethod
    async def _retrieve_message(cls, agent: "AzureAIAgent", thread_id: str, message_id: str) -> ThreadMessage | None:
        """Retrieve a message from a thread.

        Args:
            agent: The agent.
            thread_id: The thread id.
            message_id: The message id.

        Returns:
            The message or None.
        """
        message: ThreadMessage | None = None
        count = 0
        max_retries = 3

        while count < max_retries:
            try:
                message = await agent.client.agents.get_message(thread_id=thread_id, message_id=message_id)
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
        cls, kernel: "Kernel", fccs: list["FunctionCallContent"], chat_history: "ChatHistory"
    ) -> list[Any]:
        """Invoke function calls and store results in chat history."""
        tasks = [
            kernel.invoke_function_call(function_call=function_call, chat_history=chat_history)
            for function_call in fccs
        ]
        return await asyncio.gather(*tasks)

    @classmethod
    def _format_tool_outputs(
        cls, fccs: list["FunctionCallContent"], chat_history: "ChatHistory"
    ) -> list[dict[str, str]]:
        """Format tool outputs from chat history for submission.

        Args:
            fccs: The function call contents.
            chat_history: The chat history.

        Returns:
            The formatted tool outputs as a list of dictionaries.
        """
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
    async def _handle_streaming_requires_action(
        cls, agent: "AzureAIAgent", run: ThreadRun, function_steps: dict[str, "FunctionCallContent"]
    ) -> FunctionActionResult | None:
        fccs = get_function_call_contents(run, function_steps)
        if fccs:
            function_call_content = generate_function_call_content(agent_name=agent.name, fccs=fccs)

            from semantic_kernel.contents.chat_history import ChatHistory

            # TODO(evmattso): how to make sure we can support chat history reducer?
            chat_history = ChatHistory()
            _ = await cls._invoke_function_calls(fccs=fccs, chat_history=chat_history)

            function_result_content = merge_function_results(chat_history.messages)[0]

            tool_outputs = cls._format_tool_outputs(fccs, chat_history)
            return FunctionActionResult(function_call_content, function_result_content, tool_outputs)
        return None

    # endregion
