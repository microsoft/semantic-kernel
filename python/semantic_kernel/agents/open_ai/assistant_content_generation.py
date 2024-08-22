# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.text_content_block import TextContentBlock

from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException

if TYPE_CHECKING:
    from openai.resources.beta.threads.messages import Message
    from openai.resources.beta.threads.runs.runs import Run
    from openai.types.beta.threads.annotation import Annotation
    from openai.types.beta.threads.runs.tool_call import ToolCall


###################################################################
# The methods in this file are used with OpenAIAssistantAgent     #
# related code. They are used to create chat messages, or         #
# generate message content.                                       #
###################################################################


async def create_chat_message(
    client: AsyncOpenAI,
    thread_id: str,
    message: "ChatMessageContent",
    allowed_message_roles: list[str] = [AuthorRole.USER, AuthorRole.ASSISTANT],
) -> "Message":
    """Class method to add a chat message, callable from class or instance.

    Args:
        client: The client to use for creating the message.
        thread_id: The thread id.
        message: The chat message.
        allowed_message_roles: The allowed message roles.

    Returns:
        Message: The message.
    """
    if message.role.value not in allowed_message_roles:
        raise AgentExecutionException(
            f"Invalid message role `{message.role.value}`. Allowed roles are {allowed_message_roles}."
        )

    message_contents: list[dict[str, Any]] = get_message_contents(message=message)

    return await client.beta.threads.messages.create(
        thread_id=thread_id,
        role=message.role.value,  # type: ignore
        content=message_contents,  # type: ignore
    )


def get_message_contents(message: "ChatMessageContent") -> list[dict[str, Any]]:
    """Get the message contents.

    Args:
        message: The message.
    """
    contents: list[dict[str, Any]] = []
    for content in message.items:
        if isinstance(content, TextContent):
            contents.append({"type": "text", "text": content.text})
        elif isinstance(content, ImageContent) and content.uri:
            contents.append(content.to_dict())
        elif isinstance(content, FileReferenceContent):
            contents.append({
                "type": "image_file",
                "image_file": {"file_id": content.file_id},
            })
    return contents


def generate_message_content(assistant_name: str, message: "Message") -> ChatMessageContent:
    """Generate message content."""
    role = AuthorRole(message.role)

    content: ChatMessageContent = ChatMessageContent(role=role, name=assistant_name)  # type: ignore

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


def generate_function_call_content(agent_name: str, fccs: list[FunctionCallContent]) -> ChatMessageContent:
    """Generate function call content.

    Args:
        agent_name: The agent name.
        fccs: The function call contents.

    Returns:
        ChatMessageContent: The chat message content containing the function call content as the items.
    """
    return ChatMessageContent(role=AuthorRole.TOOL, name=agent_name, items=fccs)  # type: ignore


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


def generate_annotation_content(annotation: "Annotation") -> AnnotationContent:
    """Generate annotation content."""
    file_id = None
    if hasattr(annotation, "file_path"):
        file_id = annotation.file_path.file_id
    elif hasattr(annotation, "file_citation"):
        file_id = annotation.file_citation.file_id

    return AnnotationContent(
        file_id=file_id,
        quote=annotation.text,
        start_index=annotation.start_index,
        end_index=annotation.end_index,
    )
