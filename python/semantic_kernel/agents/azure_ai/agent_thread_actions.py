# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar

from azure.ai.projects.models import (
    AgentsNamedToolChoiceType,
    AgentStreamEvent,
    AsyncAgentEventHandler,
    AsyncAgentRunStream,
    OpenAIPageableListOfThreadMessage,
    OpenApiToolDefinition,
    RunStep,
    RunStepCodeInterpreterToolCall,
    RunStepDeltaChunk,
    RunStepDeltaToolCallObject,
    RunStepMessageCreationDetails,
    RunStepToolCallDetails,
    RunStepType,
    SubmitToolOutputsAction,
    ThreadMessage,
    ThreadRun,
)
from azure.ai.projects.models._enums import MessageRole

from semantic_kernel.agents.azure_ai.agent_content_generation import (
    generate_code_interpreter_content,
    generate_function_call_content,
    generate_function_result_content,
    generate_message_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_function_content,
    generate_streaming_message_content,
    get_function_call_contents,
)
from semantic_kernel.agents.azure_ai.azure_ai_agent_utils import AzureAIAgentUtils
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

    from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
    from semantic_kernel.contents import ChatHistory, ChatMessageContent
    from semantic_kernel.functions import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


# class MyEventHandler(AsyncAgentEventHandler):
#     """A single event handler that processes the entire run.

#     (and any sub-stream triggered by submit_tool_outputs_to_stream) in one place.

#     * Keep track of partial messages or completed messages in dictionaries/lists.
#     * Re-dispatch events to your custom logic for function calls, etc.
#     * If 'requires_action' -> call your _handle_streaming_requires_action and
#       call submit_tool_outputs_to_stream(..., event_handler=self) to continue in the same stream.
#     """

#     def __init__(
#         self,
#         agent_name: str,
#         thread_id: str,
#         messages_list: list,  # store final messages or streaming texts
#         function_steps: dict[str, Any],
#         project_client: "AIProjectClient",
#         kernel: "Kernel",
#     ) -> None:
#         super().__init__()
#         self.agent_name = agent_name
#         self.thread_id = thread_id
#         self.messages_list = messages_list
#         self.function_steps = function_steps  # track known function calls
#         self.project_client = project_client
#         self.kernel = kernel

#         # Keep track of run steps that created messages (like in your old code's `active_messages`)
#         self.active_messages: dict[str, RunStep] = {}
#         self._queue: asyncio.Queue = asyncio.Queue()

#     #
#     # The library calls on_event(...) behind the scenes, but these typed
#     # methods can be recognized by the base event handler to handle specific events:
#     #

#     async def on_thread_run_created(self, run: ThreadRun) -> None:
#         logger.info(f"[Handler] Run created with ID: {run.id}")

#     async def on_thread_run_in_progress(self, step: RunStep) -> None:
#         logger.info(f"[Handler] Run in-progress with step ID: {step.id}")

#     async def on_thread_message_delta(self, delta: MessageDeltaChunk) -> None:
#         # This is your partial streaming text. Convert it to a final string or store it.
#         content = generate_streaming_message_content(self.agent_name, delta)
#         logger.info(f"[Handler] on_thread_message_delta -> {content}")
#         # You could yield this up to a caller, or store in self.messages_list
#         self.messages_list.append(content)
#         self._queue.put_nowait(content)

#     async def on_run_step_completed(self, step: RunStep) -> None:
#         """The run step has completed. If it created a message, store it in active_messages so we can retrieve content later."""
#         logger.info(f"[Handler] Run step completed with ID: {step.id}")
#         if hasattr(step.step_details, "message_creation") and step.step_details.message_creation:
#             message_id = step.step_details.message_creation.message_id
#             if message_id not in self.active_messages:
#                 self.active_messages[message_id] = step
#                 self._queue.put_nowait(step)

#     async def on_run_step_delta(self, chunk: Any) -> None:
#         """This can be used for partial step updates, including partial tool calls."""
#         run_step_event_data: RunStepDeltaChunk = chunk
#         run_step_details = run_step_event_data.delta.step_details
#         if isinstance(run_step_details, RunStepDeltaToolCallObject):
#             for tool_call in run_step_details.tool_calls:
#                 tool_content = None
#                 if tool_call.type == "function":
#                     tool_content = generate_streaming_function_content(self.agent_name, run_step_details)
#                 elif tool_call.type == "code_interpreter":
#                     tool_content = generate_streaming_code_interpreter_content(self.agent_name, run_step_details)
#                 if tool_content:
#                     self._queue.put_nowait(tool_content)
#         # if hasattr(chunk.delta, "step_details") and chunk.delta.step_details:
#         #     step_details = chunk.delta.step_details
#         #     if hasattr(step_details, "tool_calls") and step_details.tool_calls:
#         #         for tool_call in step_details.tool_calls:
#         #             if tool_call.type == "function":
#         #                 content = generate_streaming_function_content(self.agent_name, tool_call)
#         #                 self.messages_list.append(content)
#         #                 self._queue.put_nowait(content)
#         #             elif tool_call.type == "code_interpreter":
#         #                 content = generate_streaming_code_interpreter_content(self.agent_name, tool_call)
#         #                 self.messages_list.append(content)
#         #                 self._queue.put_nowait(content)

#     async def on_thread_run_requires_action(self, run: ThreadRun) -> None:
#         """The run is waiting for tool outputs or function calls.

#         This is analogous to
#         'THREAD_RUN_REQUIRES_ACTION' in your old code. We'll call out to your custom
#         _handle_streaming_requires_action and then re-submit tool outputs.
#         """
#         logger.info(f"[Handler] Run requires action with ID: {run.id}")
#         # Suppose you have a custom method that decides how to respond:
#         action_result = await AgentThreadActions._handle_streaming_requires_action(
#             agent_name=self.agent_name,
#             kernel=self.kernel,
#             run=run,
#             function_steps=self.function_steps,
#         )
#         if not action_result:
#             logger.error("Function call required but no function steps found!")
#             return  # or raise

#         # If there's a function result to yield to your user, store it
#         if action_result.function_result_content:
#             self.messages_list.append(action_result.function_result_content)

#         # If there's a next function call (or more tool outputs), we must submit them
#         if action_result.function_call_content:
#             self.messages_list.append(str(action_result.function_call_content))

#         if action_result.tool_outputs:
#             logger.info(f"[Handler] Submitting {len(action_result.tool_outputs)} tool outputs...")
#             # Notice we re-use *this* same event handler so that subsequent streaming
#             # continues to arrive in these callback methods.
#             await self.project_client.agents.submit_tool_outputs_to_stream(
#                 thread_id=run.thread_id,
#                 run_id=run.id,
#                 tool_outputs=action_result.tool_outputs,
#                 event_handler=self,  # critical - continue in the same event handler
#             )

#     async def on_thread_run_completed(self, run: ThreadRun) -> None:
#         """The run is finished. We can retrieve any final messages.

#         Then the library will eventually call on_done().
#         """
#         logger.info(f"[Handler] Run completed with ID: {run.id}")
#         # Retrieve all final messages from active_messages
#         for message_id, step in self.active_messages.items():
#             message_obj = await AgentThreadActions._retrieve_message(self.agent_name, run.thread_id, message_id)
#             if message_obj and hasattr(message_obj, "content"):
#                 content = generate_message_content(self.agent_name, message_obj, step)
#                 self.messages_list.append(content)
#                 self._queue.put_nowait(content)

#     async def on_thread_run_failed(self, run: ThreadRun) -> None:
#         """The run has failed. Log or handle error details."""
#         msg = run.last_error.message if (run.last_error and run.last_error.message) else ""
#         logger.error(f"[Handler] Run failed with ID: {run.id}, error: {msg}")
#         self._queue.put_nowait(msg)

#     async def on_done(self) -> None:
#         """The entire stream is done (server sent `data: [DONE]` or the run entered a final state)."""
#         logger.info("[Handler] on_done called, streaming is complete.")
#         self._queue.put_nowait("[DONE]")

#     #
#     # Optional overrides if you need to see raw event data
#     # or other event types that don't have a dedicated callback:
#     #
#     async def on_unhandled_event(self, event_type: str, event_data: Any) -> None:
#         logger.debug(f"[Handler] Unhandled event: {event_type}, data={event_data}")

#     async def stream_messages(self) -> AsyncIterator[Any]:
#         while True:
#             item = await self._queue.get()
#             if item == "[DONE]":
#                 break
#             yield item


# async def _consume_stream(stream) -> None:
#     """Consumes the SSE stream so the event handler gets invoked for each event.
#     We do 'async with stream' and 'async for ... in stream' to pull all events.
#     """
#     async with stream as response_stream:
#         async for _event_type, _event_data, _raw_event in response_stream:
#             pass
#     # Once we exit this block, we've consumed all SSE events


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
        arguments = {} if arguments is None else {**arguments, **kwargs}
        kernel = kernel or agent.kernel

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
            run = await cls._poll_run_status(agent=agent, run=run, thread_id=thread_id)

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

                    chat_history = ChatHistory() if kwargs.get("chat_history") is None else kwargs["chat_history"]
                    _ = await cls._invoke_function_calls(kernel=kernel, fccs=fccs, chat_history=chat_history)

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
                match completed_step.type:
                    case RunStepType.TOOL_CALLS:
                        logger.debug(
                            f"Entering step type tool_calls for run [{run.id}], agent `{agent.name}` and "
                            f"thread `{thread_id}`"
                        )
                        tool_call_details: RunStepToolCallDetails = completed_step.step_details
                        for tool_call in tool_call_details.tool_calls:
                            is_visible = False
                            content: "ChatMessageContent | None" = None
                            match tool_call.type:
                                case AgentsNamedToolChoiceType.CODE_INTERPRETER:
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
                                case AgentsNamedToolChoiceType.FUNCTION:
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
                                            f"Yielding tool_message for run [{run.id}], agent `{agent.name}` and "
                                            f"thread `{thread_id}` and message count `{message_count}`, "
                                            f"is_visible `{is_visible}`"
                                        )
                                        yield is_visible, content
                    case RunStepType.MESSAGE_CREATION:
                        logger.debug(
                            f"Entering step type message_creation for run [{run.id}], agent `{agent.name}` and "
                            f"thread `{thread_id}`"
                        )
                        message_call_details: RunStepMessageCreationDetails = completed_step.step_details
                        message = await cls._retrieve_message(
                            agent=agent,
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
        messages: list[Any],
        arguments: Any,
        kernel: Any,
        **kwargs: Any,
    ) -> AsyncIterable[str]:
        """Invoke the agent stream and yield ChatMessageContent continuously."""
        # Prepare and merge arguments.
        arguments = {} if arguments is None else {**arguments, **kwargs}
        kernel = kernel or agent.kernel
        arguments = agent.merge_arguments(arguments)

        # Retrieve tools and build instructions.
        tools = cls._get_tools(agent, kernel, is_async=True)
        instructions = await agent.format_instructions(kernel=kernel, arguments=arguments)

        # Kick off the streaming run.
        stream: AsyncAgentRunStream = await agent.client.agents.create_stream(
            assistant_id=agent.id,
            thread_id=thread_id,
            instructions=instructions,
            tools=tools,
        )

        function_steps: dict[str, FunctionCallContent] = {}
        active_messages: dict[str, RunStep] = {}

        # Process events from the primary stream.
        async for content in cls._process_stream_events(
            stream, agent, thread_id, messages, kernel, function_steps, active_messages
        ):
            yield content

    @classmethod
    async def _process_stream_events(
        cls,
        stream: AsyncAgentRunStream,
        agent: "AzureAIAgent",
        thread_id: str,
        messages: list[Any],
        kernel: Any,
        function_steps: dict[str, FunctionCallContent],
        active_messages: dict[str, RunStep],
    ) -> AsyncIterable[str]:
        """Process events from the main stream and delegate tool output handling as needed."""
        while True:
            async with stream as response_stream:
                async for event_type, event_data, _ in response_stream:
                    if event_type == AgentStreamEvent.THREAD_RUN_CREATED:
                        run: ThreadRun = event_data
                        logger.info(f"Assistant run created with ID: {run.id}")

                    elif event_type == AgentStreamEvent.THREAD_RUN_IN_PROGRESS:
                        run_step: RunStep = event_data
                        logger.info(f"Assistant run in progress with ID: {run_step.id}")

                    elif event_type == AgentStreamEvent.THREAD_MESSAGE_DELTA:
                        yield generate_streaming_message_content(agent.name, event_data)

                    elif event_type == AgentStreamEvent.THREAD_RUN_STEP_COMPLETED:
                        step_completed: RunStep = event_data
                        logger.info(f"Run step completed with ID: {step_completed.id}")
                        if isinstance(step_completed.step_details, RunStepMessageCreationDetails):
                            msg_id = step_completed.step_details.message_creation.message_id
                            active_messages.setdefault(msg_id, step_completed)

                    elif event_type == AgentStreamEvent.THREAD_RUN_STEP_DELTA:
                        run_step_event: RunStepDeltaChunk = event_data
                        details = run_step_event.delta.step_details
                        if isinstance(details, RunStepDeltaToolCallObject):
                            for tool_call in details.tool_calls:
                                content = None
                                if tool_call.type == "function":
                                    content = generate_streaming_function_content(agent.name, details)
                                elif tool_call.type == "code_interpreter":
                                    content = generate_streaming_code_interpreter_content(agent.name, details)
                                if content:
                                    yield content

                    elif event_type == AgentStreamEvent.THREAD_RUN_REQUIRES_ACTION:
                        run: ThreadRun = event_data
                        action_result = await cls._handle_streaming_requires_action(
                            agent_name=agent.name,
                            kernel=kernel,
                            run=run,
                            function_steps=function_steps,
                        )
                        if action_result is None:
                            raise RuntimeError(
                                f"Function call required but no function steps found for agent `{agent.name}` "
                                f"thread: {thread_id}."
                            )

                        if action_result.function_result_content:
                            yield action_result.function_result_content
                            if messages:
                                messages.append(action_result.function_result_content)

                        if action_result.function_call_content:
                            if messages:
                                messages.append(action_result.function_call_content)
                            async for sub_content in cls._stream_tool_outputs(
                                agent, thread_id, run, action_result, active_messages, messages
                            ):
                                yield sub_content
                            break

                    elif event_type == AgentStreamEvent.THREAD_RUN_COMPLETED:
                        run: ThreadRun = event_data
                        logger.info(f"Run completed with ID: {run.id}")
                        if active_messages:
                            for msg_id, step in active_messages.items():
                                message = await cls._retrieve_message(
                                    agent=agent, thread_id=thread_id, message_id=msg_id
                                )
                                if message and hasattr(message, "content"):
                                    final_content = generate_message_content(agent.name, message, step)
                                    if messages:
                                        messages.append(final_content)
                        return

                    elif event_type == AgentStreamEvent.THREAD_RUN_FAILED:
                        run_failed: ThreadRun = event_data
                        error_message = (
                            run_failed.last_error.message
                            if run_failed.last_error and run_failed.last_error.message
                            else ""
                        )
                        raise RuntimeError(
                            f"Run failed with status: `{run_failed.status}` for agent `{agent.name}` "
                            f"thread `{thread_id}` with error: {error_message}"
                        )
                else:
                    break
        return

    @classmethod
    async def _stream_tool_outputs(
        cls,
        agent: "AzureAIAgent",
        thread_id: str,
        run: ThreadRun,
        action_result: FunctionActionResult,
        active_messages: dict[str, RunStep],
        messages: list[Any],
    ) -> AsyncIterable[str]:
        """Wraps the tool outputs stream as an async generator.

        This allows downstream consumers to iterate over the yielded content.
        """
        handler = AsyncAgentEventHandler()
        await agent.client.agents.submit_tool_outputs_to_stream(
            run_id=run.id,
            thread_id=thread_id,
            tool_outputs=action_result.tool_outputs,  # type: ignore
            event_handler=handler,
        )
        async for sub_event_type, sub_event_data, _ in handler:
            if sub_event_type == AgentStreamEvent.THREAD_MESSAGE_DELTA:
                yield generate_streaming_message_content(agent.name, sub_event_data)
            elif sub_event_type == AgentStreamEvent.THREAD_RUN_COMPLETED:
                logger.info(f"Run completed with ID: {sub_event_data.id}")
                if active_messages:
                    for msg_id, step in active_messages.items():
                        message = await cls._retrieve_message(agent=agent, thread_id=thread_id, message_id=msg_id)
                        if message and hasattr(message, "content"):
                            final_content = generate_message_content(agent.name, message, step)
                            messages.append(final_content)
                return
            elif sub_event_type == AgentStreamEvent.THREAD_RUN_FAILED:
                run_failed: ThreadRun = sub_event_data
                error_message = (
                    run_failed.last_error.message if run_failed.last_error and run_failed.last_error.message else ""
                )
                raise RuntimeError(
                    f"Run failed with status: `{run_failed.status}` for agent `{agent.name}` "
                    f"thread `{thread_id}` with error: {error_message}"
                )
            elif sub_event_type == AgentStreamEvent.DONE:
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
        client: "AIProjectClient",
        thread_id: str,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Get messages from a thread."""
        agent_names: dict[str, Any] = {}
        last_id: str | None = None
        messages: OpenAIPageableListOfThreadMessage = None

        while True:
            messages = await client.agents.list_messages(
                thread_id=thread_id,
                run_id=None,
                limit=None,
                order="desc",
                after=last_id,
                before=None,
            )

            if not messages:
                break

            for message in messages.data:
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
                content = generate_message_content(assistant_name, message)

                # Only yield if there are actual items in the content
                if len(content.items) > 0:
                    yield content

            # Check if there are more messages to fetch
            if not messages.has_more:
                break

    # endregion

    # region Internal Methods

    @classmethod
    def _get_tools(cls, agent: "AzureAIAgent", kernel: "Kernel", is_async: bool = False) -> list[dict[str, Any]]:
        """In *both* cases, return a list of dict describing the function schema.

        No references to AsyncFunctionTool or sets of callables.
        """
        tools = []
        # Start with the agent's built-in tools (already dict-based).
        for t in agent.definition.tools:
            if t.get("type") == "openapi":
                openapi_data = t["openapi"]  # Extract full OpenAPI definition
                # Ensure only the required field is passed
                tools.append(OpenApiToolDefinition(openapi=openapi_data))
            else:
                tools.extend(agent.definition.tools)  # typically a list of dict

        # Then add kernel function metadata as dict
        funcs = kernel.get_full_list_of_function_metadata()
        dict_defs = [kernel_function_metadata_to_function_call_format(f) for f in funcs]
        tools.extend(dict_defs)

        return tools

    # @classmethod
    # def _get_tools(cls, agent: "AzureAIAgent", kernel: "Kernel", is_async: bool = False) -> Any:
    #     """Get the list of tools for the agent.

    #     The return type differs in async vs. non-async:
    #     • Non-async: returns a list of dict-based function definitions
    #     • Async: returns an AsyncToolSet containing an AsyncFunctionTool
    #     """
    #     if not is_async:
    #         # Original synchronous approach:
    #         #  - Start with any built-in tool definitions
    #         #  - Extend with Redwood-friendly dict for each kernel function
    #         tools = []
    #         tools.extend(agent.definition.tools)  # typically a list of dict
    #         funcs = kernel.get_full_list_of_function_metadata()  # however you get them
    #         tools.extend([kernel_function_metadata_to_function_call_format(f) for f in funcs])
    #         return tools

    #     # Asynchronous approach:
    #     #  We want an AsyncFunctionTool, which expects a set of real Python callables.
    #     #  So we have to gather the actual functions from the kernel, not dicts.
    #     #  Let's assume `kernel.get_full_list_of_function_metadata()` returns some metadata
    #     #  for which we can retrieve actual Python callables.
    #     funcs_metadata = kernel.get_full_list_of_function_metadata()

    #     # Convert the metadata objects into actual Python callables
    #     # (You have to implement this method to suit your environment.)
    #     async_funcs = set()
    #     for f_meta in funcs_metadata:
    #         actual_callable = cls._get_python_callable_from_metadata(kernel, f_meta)
    #         async_funcs.add(actual_callable)

    #     # Create the AsyncFunctionTool with that set of callables
    #     async_tool = AsyncFunctionTool(async_funcs)

    #     # Put it in an AsyncToolSet (assuming Redwood’s AsyncToolSet usage)
    #     toolset = AsyncToolSet()
    #     toolset.add(async_tool)
    #     return toolset

    @classmethod
    async def _poll_run_status(cls, agent: "AzureAIAgent", run: ThreadRun, thread_id: str) -> ThreadRun:
        """Poll the run status."""
        logger.info(f"Polling run status: {run.id}, threadId: {thread_id}")

        count = 0
        try:
            run = await asyncio.wait_for(
                cls._poll_loop(agent=agent, run=run, thread_id=thread_id, count=count),
                timeout=agent.polling_options.run_polling_timeout.total_seconds(),
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
        cls,
        agent_name: str,
        kernel: "Kernel",
        run: ThreadRun,
        function_steps: dict[str, "FunctionCallContent"],
        **kwargs: Any,
    ) -> FunctionActionResult | None:
        fccs = get_function_call_contents(run, function_steps)
        if fccs:
            function_call_content = generate_function_call_content(agent_name=agent_name, fccs=fccs)

            from semantic_kernel.contents.chat_history import ChatHistory

            chat_history = ChatHistory() if kwargs.get("chat_history") is None else kwargs["chat_history"]
            _ = await cls._invoke_function_calls(kernel=kernel, fccs=fccs, chat_history=chat_history)

            function_result_content = merge_function_results(chat_history.messages)[0]

            tool_outputs = cls._format_tool_outputs(fccs, chat_history)
            return FunctionActionResult(function_call_content, function_result_content, tool_outputs)
        return None

    # endregion
