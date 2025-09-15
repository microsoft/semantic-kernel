# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI
from openai.types.beta.threads.file_citation_annotation import FileCitationAnnotation
from openai.types.beta.threads.file_citation_delta_annotation import FileCitationDeltaAnnotation
from openai.types.beta.threads.file_path_annotation import FilePathAnnotation
from openai.types.beta.threads.file_path_delta_annotation import FilePathDeltaAnnotation
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.image_file_delta_block import ImageFileDeltaBlock
from openai.types.beta.threads.message_delta_event import MessageDeltaEvent
from openai.types.beta.threads.runs import CodeInterpreterLogs
from openai.types.beta.threads.runs.code_interpreter_tool_call import CodeInterpreterOutputImage
from openai.types.beta.threads.text_content_block import TextContentBlock
from openai.types.beta.threads.text_delta_block import TextDeltaBlock

from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from openai.types.beta.threads.message import Message
    from openai.types.beta.threads.run import Run
    from openai.types.beta.threads.runs import RunStep
    from openai.types.beta.threads.runs.tool_call import ToolCall
    from openai.types.beta.threads.runs.tool_calls_step_details import ToolCallsStepDetails


###################################################################
# The methods in this file are used with OpenAIAssistantAgent     #
# related code. They are used to create chat messages, or         #
# generate message content.                                       #
###################################################################


@experimental
async def create_chat_message(
    client: AsyncOpenAI,
    thread_id: str,
    message: "ChatMessageContent",
    allowed_message_roles: Sequence[str] | None = None,
) -> "Message":
    """Class method to add a chat message, callable from class or instance.

    Args:
        client: The client to use for creating the message.
        thread_id: The thread id.
        message: The chat message.
        allowed_message_roles: The allowed message roles.
            Defaults to [AuthorRole.USER, AuthorRole.ASSISTANT] if None.
            Providing an empty list will disallow all message roles.

    Returns:
        Message: The message.
    """
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
    )


@experimental
def get_message_contents(message: "ChatMessageContent") -> list[dict[str, Any]]:
    """Get the message contents.

    Args:
        message: The message.
    """
    contents: list[dict[str, Any]] = []
    for content in message.items:
        match content:
            case TextContent():
                # Make sure text is a string
                final_text = content.text
                if not isinstance(final_text, str):
                    if isinstance(final_text, (list, tuple)):
                        final_text = " ".join(map(str, final_text))
                    else:
                        final_text = str(final_text)

                contents.append({"type": "text", "text": final_text})

            case ImageContent():
                if content.uri:
                    contents.append(content.to_dict())

            case FileReferenceContent():
                contents.append({
                    "type": "image_file",
                    "image_file": {"file_id": content.file_id},
                })

            case FunctionResultContent():
                final_result = content.result
                match final_result:
                    case str():
                        contents.append({"type": "text", "text": final_result})
                    case list() | tuple():
                        contents.append({"type": "text", "text": " ".join(map(str, final_result))})
                    case _:
                        contents.append({"type": "text", "text": str(final_result)})

    return contents


@experimental
def generate_message_content(
    assistant_name: str, message: "Message", completed_step: "RunStep | None" = None
) -> ChatMessageContent:
    """Generate message content."""
    role = AuthorRole(message.role)

    metadata = (
        {
            "created_at": completed_step.created_at,
            "message_id": message.id,  # message needs to be defined in context
            "step_id": completed_step.id,
            "run_id": completed_step.run_id,
            "thread_id": completed_step.thread_id,
            "assistant_id": completed_step.assistant_id,
            "usage": completed_step.usage,
        }
        if completed_step is not None
        else None
    )

    content: ChatMessageContent = ChatMessageContent(role=role, name=assistant_name, metadata=metadata)  # type: ignore

    for item_content in message.content:
        if item_content.type == "text":
            assert isinstance(item_content, TextContentBlock)  # nosec
            content.items.append(
                TextContent(
                    text=item_content.text.value,
                )
            )
            for annotation in item_content.text.annotations:
                content.items.append(generate_annotation_content(annotation))
        elif item_content.type == "image_file":
            assert isinstance(item_content, ImageFileContentBlock)  # nosec
            content.items.append(
                FileReferenceContent(
                    file_id=item_content.image_file.file_id,
                )
            )
    return content


@experimental
def generate_streaming_message_content(
    assistant_name: str,
    message_delta_event: "MessageDeltaEvent",
    completed_step: "RunStep | None" = None,
) -> StreamingChatMessageContent:
    """Generate streaming message content from a MessageDeltaEvent."""
    delta = message_delta_event.delta

    metadata = (
        {
            "created_at": completed_step.created_at,
            "message_id": message_delta_event.id,  # message needs to be defined in context
            "step_id": completed_step.id,
            "run_id": completed_step.run_id,
            "thread_id": completed_step.thread_id,
            "assistant_id": completed_step.assistant_id,
            "usage": completed_step.usage,
        }
        if completed_step is not None
        else None
    )

    # Determine the role
    role = AuthorRole(delta.role) if delta.role is not None else AuthorRole("assistant")

    items: list[StreamingTextContent | StreamingAnnotationContent | StreamingFileReferenceContent] = []

    # Process each content block in the delta
    for delta_block in delta.content or []:
        if delta_block.type == "text":
            assert isinstance(delta_block, TextDeltaBlock)  # nosec
            if delta_block.text and delta_block.text.value:  # Ensure text is not None
                text_value = delta_block.text.value
                items.append(
                    StreamingTextContent(
                        text=text_value,
                        choice_index=delta_block.index,
                    )
                )
                # Process annotations if any
                if delta_block.text.annotations:
                    for annotation in delta_block.text.annotations or []:
                        if isinstance(annotation, (FileCitationDeltaAnnotation, FilePathDeltaAnnotation)):
                            items.append(generate_streaming_annotation_content(annotation))
        elif delta_block.type == "image_file":
            assert isinstance(delta_block, ImageFileDeltaBlock)  # nosec
            if delta_block.image_file and delta_block.image_file.file_id:
                file_id = delta_block.image_file.file_id
                items.append(
                    StreamingFileReferenceContent(
                        file_id=file_id,
                    )
                )

    return StreamingChatMessageContent(role=role, name=assistant_name, items=items, choice_index=0, metadata=metadata)  # type: ignore


@experimental
def generate_final_streaming_message_content(
    assistant_name: str,
    message: "Message",
    completed_step: "RunStep | None" = None,
) -> StreamingChatMessageContent:
    """Generate streaming message content from a MessageDeltaEvent."""
    metadata = (
        {
            "created_at": completed_step.created_at,
            "message_id": message.id,  # message needs to be defined in context
            "step_id": completed_step.id,
            "run_id": completed_step.run_id,
            "thread_id": completed_step.thread_id,
            "assistant_id": completed_step.assistant_id,
            "usage": completed_step.usage,
        }
        if completed_step is not None
        else None
    )

    # Determine the role
    role = AuthorRole(message.role) if message.role is not None else AuthorRole("assistant")

    items: list[StreamingTextContent | StreamingAnnotationContent | StreamingFileReferenceContent] = []

    # Process each content block in the delta
    for item_content in message.content:
        if item_content.type == "text":
            assert isinstance(item_content, TextContentBlock)  # nosec
            items.append(StreamingTextContent(text=item_content.text.value, choice_index=0))
            for annotation in item_content.text.annotations:
                items.append(generate_streaming_annotation_content(annotation))
        elif item_content.type == "image_file":
            assert isinstance(item_content, ImageFileContentBlock)  # nosec
            items.append(
                StreamingFileReferenceContent(
                    file_id=item_content.image_file.file_id,
                )
            )

    return StreamingChatMessageContent(role=role, name=assistant_name, items=items, choice_index=0, metadata=metadata)  # type: ignore


@experimental
def merge_function_results(messages: list["ChatMessageContent"], name: str) -> "ChatMessageContent":
    """Combine multiple function result content types to one chat message content type.

    This method combines the FunctionResultContent items from separate ChatMessageContent messages,
    and is used in the event that the `context.terminate = True` condition is met.

    Args:
        messages: The list of chat messages.
        name: The name of the agent.

    Returns:
        list[ChatMessageContent]: The combined chat message content.
    """
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_result_content import FunctionResultContent

    items: list[Any] = []
    for message in messages:
        items.extend([item for item in message.items if isinstance(item, FunctionResultContent)])
    return ChatMessageContent(
        role=AuthorRole.TOOL,
        items=items,
        name=name,
    )


@experimental
def merge_streaming_function_results(
    messages: list["ChatMessageContent | StreamingChatMessageContent"],
    name: str,
    ai_model_id: str | None = None,
    function_invoke_attempt: int | None = None,
) -> "StreamingChatMessageContent":
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
    from semantic_kernel.contents.function_result_content import FunctionResultContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

    items: list[Any] = []
    for message in messages:
        items.extend([item for item in message.items if isinstance(item, FunctionResultContent)])

    return StreamingChatMessageContent(
        name=name,
        role=AuthorRole.TOOL,
        items=items,
        choice_index=0,
        ai_model_id=ai_model_id,
        function_invoke_attempt=function_invoke_attempt,
    )


@experimental
def generate_function_call_content(agent_name: str, fccs: list[FunctionCallContent]) -> ChatMessageContent:
    """Generate function call content.

    Args:
        agent_name: The agent name.
        fccs: The function call contents.

    Returns:
        ChatMessageContent: The chat message content containing the function call content as the items.
    """
    return ChatMessageContent(role=AuthorRole.ASSISTANT, name=agent_name, items=fccs)  # type: ignore


@experimental
def generate_function_result_content(
    agent_name: str, function_step: FunctionCallContent, tool_call: "ToolCall"
) -> ChatMessageContent:
    """Generate function result content."""
    function_call_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.TOOL, name=agent_name)  # type: ignore
    function_call_content.items.append(
        FunctionResultContent(
            function_name=function_step.function_name,
            plugin_name=function_step.plugin_name,
            id=function_step.id,
            result=tool_call.function.output,  # type: ignore
        )
    )
    return function_call_content


@experimental
def get_function_call_contents(run: "Run", function_steps: dict[str, FunctionCallContent]) -> list[FunctionCallContent]:
    """Extract function call contents from the run.

    Args:
        run: The run.
        function_steps: The function steps

    Returns:
        The list of function call contents.
    """
    function_call_contents: list[FunctionCallContent] = []
    required_action = getattr(run, "required_action", None)
    if not required_action or not getattr(required_action, "submit_tool_outputs", False):
        return function_call_contents
    for tool in required_action.submit_tool_outputs.tool_calls:
        fcc = FunctionCallContent(
            id=tool.id,
            index=getattr(tool, "index", None),
            name=tool.function.name,
            arguments=tool.function.arguments,
        )
        function_call_contents.append(fcc)
        function_steps[tool.id] = fcc
    return function_call_contents


@experimental
def generate_code_interpreter_content(agent_name: str, code: str) -> "ChatMessageContent":
    """Generate code interpreter content.

    Args:
        agent_name: The agent name.
        code: The code.

    Returns:
        ChatMessageContent: The chat message content.
    """
    return ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        content=code,
        name=agent_name,
        metadata={"code": True},
    )


@experimental
def generate_streaming_function_content(
    agent_name: str, step_details: "ToolCallsStepDetails"
) -> "StreamingChatMessageContent":
    """Generate streaming function content.

    Args:
        agent_name: The agent name.
        step_details: The function step.

    Returns:
        StreamingChatMessageContent: The chat message content.
    """
    items: list[FunctionCallContent] = []

    for tool in step_details.tool_calls:
        if tool.type == "function":
            items.append(
                FunctionCallContent(
                    id=tool.id,
                    index=getattr(tool, "index", None),
                    name=tool.function.name,
                    arguments=tool.function.arguments,
                )
            )

    return (
        StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            name=agent_name,
            items=items,  # type: ignore
            choice_index=0,
        )
        if len(items) > 0
        else None
    )


@experimental
def generate_streaming_code_interpreter_content(
    agent_name: str, step_details: "ToolCallsStepDetails"
) -> "StreamingChatMessageContent | None":
    """Generate code interpreter content.

    Args:
        agent_name: The agent name.
        step_details: The current step details.

    Returns:
        StreamingChatMessageContent: The chat message content.
    """
    items: list[StreamingTextContent | StreamingFileReferenceContent] = []

    metadata: dict[str, bool] = {}
    for index, tool in enumerate(step_details.tool_calls):
        if tool.type == "code_interpreter":
            if tool.code_interpreter.input:
                items.append(
                    StreamingTextContent(
                        choice_index=index,
                        text=tool.code_interpreter.input,
                    )
                )
                metadata["code"] = True
            if tool.code_interpreter.outputs:
                for output in tool.code_interpreter.outputs:
                    if isinstance(output, CodeInterpreterOutputImage) and output.image.file_id:
                        items.append(
                            StreamingFileReferenceContent(
                                file_id=output.image.file_id,
                            )
                        )
                    if isinstance(output, CodeInterpreterLogs) and output.logs:
                        items.append(
                            StreamingTextContent(
                                choice_index=index,
                                text=output.logs,
                            )
                        )

    return (
        StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            name=agent_name,
            items=items,  # type: ignore
            choice_index=0,
            metadata=metadata if metadata else None,
        )
        if len(items) > 0
        else None
    )


@experimental
def generate_annotation_content(annotation: FileCitationAnnotation | FilePathAnnotation) -> AnnotationContent:
    """Generate annotation content."""
    file_id = None
    match annotation:
        case FilePathAnnotation():
            file_id = annotation.file_path.file_id
        case FileCitationAnnotation():
            file_id = annotation.file_citation.file_id

    return AnnotationContent(
        file_id=file_id,
        quote=annotation.text,
        start_index=annotation.start_index,
        end_index=annotation.end_index,
    )


@experimental
def generate_streaming_annotation_content(
    annotation: FileCitationAnnotation | FilePathAnnotation | FilePathDeltaAnnotation | FileCitationDeltaAnnotation,
) -> StreamingAnnotationContent:
    """Generate streaming annotation content."""
    file_id = None
    match annotation:
        case FilePathAnnotation():
            file_id = annotation.file_path.file_id
        case FileCitationAnnotation():
            file_id = annotation.file_citation.file_id
        case FilePathDeltaAnnotation():
            file_id = annotation.file_path.file_id if annotation.file_path is not None else None
        case FileCitationDeltaAnnotation():
            file_id = annotation.file_citation.file_id if annotation.file_citation is not None else None

    return StreamingAnnotationContent(
        file_id=file_id,
        quote=annotation.text,
        start_index=annotation.start_index,
        end_index=annotation.end_index,
    )


@experimental
def generate_function_call_streaming_content(
    agent_name: str,
    fccs: list[FunctionCallContent],
) -> StreamingChatMessageContent:
    """Generate function call content.

    Args:
        agent_name: The agent name.
        fccs: The function call contents.

    Returns:
        StreamingChatMessageContent: The chat message content containing the function call content as the items.
    """
    return StreamingChatMessageContent(role=AuthorRole.ASSISTANT, choice_index=0, name=agent_name, items=fccs)  # type: ignore
