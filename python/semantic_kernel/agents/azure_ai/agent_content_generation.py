# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any, cast

from azure.ai.agents.models import (
    MessageDeltaImageFileContent,
    MessageDeltaImageFileContentObject,
    MessageDeltaTextContent,
    MessageDeltaTextFileCitationAnnotation,
    MessageDeltaTextFilePathAnnotation,
    MessageDeltaTextUrlCitationAnnotation,
    MessageImageFileContent,
    MessageTextContent,
    MessageTextFileCitationAnnotation,
    MessageTextFilePathAnnotation,
    MessageTextUrlCitationAnnotation,
    RequiredFunctionToolCall,
    RunStep,
    RunStepAzureAISearchToolCall,
    RunStepBingGroundingToolCall,
    RunStepDeltaCodeInterpreterImageOutput,
    RunStepDeltaCodeInterpreterLogOutput,
    RunStepDeltaCodeInterpreterToolCall,
    RunStepDeltaFileSearchToolCall,
    RunStepDeltaFunctionToolCall,
    RunStepFileSearchToolCall,
    RunStepFunctionToolCall,
    RunStepOpenAPIToolCall,
    ThreadMessage,
    ThreadRun,
)

from semantic_kernel.contents.annotation_content import AnnotationContent, CitationType
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
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from azure.ai.agents.models import (
        MessageDeltaChunk,
        RunStepDeltaToolCallObject,
    )

"""
The methods in this file are used with Azure AI Agent
related code. They are used to invoke, create chat messages,
or generate message content.
"""


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
    assistant_name: str, message: "ThreadMessage", completed_step: "RunStep | None" = None
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
            "agent_id": completed_step.agent_id,
            "usage": completed_step.usage,
        }
        if completed_step is not None
        else None
    )

    content: ChatMessageContent = ChatMessageContent(role=role, name=assistant_name, metadata=metadata)  # type: ignore

    messages: list[MessageImageFileContent | MessageTextContent] = cast(
        list[MessageImageFileContent | MessageTextContent], message.content or []
    )
    for item_content in messages:
        if item_content.type == "text":
            content.items.append(
                TextContent(
                    text=item_content.text.value,
                )
            )
            for annotation in item_content.text.annotations:
                content.items.append(generate_annotation_content(annotation))  # type: ignore
        elif item_content.type == "image_file":
            content.items.append(
                FileReferenceContent(
                    file_id=item_content.image_file.file_id,
                )
            )
    return content


@experimental
def generate_streaming_message_content(
    assistant_name: str, message_delta_event: "MessageDeltaChunk"
) -> StreamingChatMessageContent:
    """Generate streaming message content from a MessageDeltaEvent."""
    delta = message_delta_event.delta

    # Determine the role
    role = AuthorRole(delta.role) if delta.role is not None else AuthorRole("assistant")

    items: list[StreamingTextContent | StreamingAnnotationContent | StreamingFileReferenceContent] = []

    delta_chunks: list[MessageDeltaImageFileContent | MessageDeltaTextContent] = cast(
        list[MessageDeltaImageFileContent | MessageDeltaTextContent], delta.content or []
    )

    for delta_block in delta_chunks:
        if delta_block.type == "text":
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
                        if isinstance(
                            annotation,
                            (
                                MessageDeltaTextFileCitationAnnotation,
                                MessageDeltaTextFilePathAnnotation,
                                MessageDeltaTextUrlCitationAnnotation,
                            ),
                        ):
                            items.append(generate_streaming_annotation_content(annotation))
        elif delta_block.type == "image_file":
            assert isinstance(delta_block, MessageDeltaImageFileContent)  # nosec
            if delta_block.image_file and isinstance(delta_block.image_file, MessageDeltaImageFileContentObject):
                file_id = delta_block.image_file.file_id
                items.append(
                    StreamingFileReferenceContent(
                        file_id=file_id,
                    )
                )

    return StreamingChatMessageContent(role=role, name=assistant_name, items=items, choice_index=0)  # type: ignore


@experimental
def get_function_call_contents(
    run: "ThreadRun", function_steps: dict[str, FunctionCallContent]
) -> list[FunctionCallContent]:
    """Extract function call contents from the run.

    Args:
        run: The run.
        function_steps: The function steps

    Returns:
        The list of function call contents.
    """
    function_call_contents: list[FunctionCallContent] = []
    required_action = getattr(run, "required_action", None)
    submit_tool_outputs = getattr(required_action, "submit_tool_outputs", None)
    if not submit_tool_outputs or not hasattr(submit_tool_outputs, "tool_calls"):
        return function_call_contents
    tool_calls = getattr(submit_tool_outputs, "tool_calls", [])
    if not isinstance(tool_calls, (list, tuple)):
        return function_call_contents
    for tool_call in tool_calls:
        if not isinstance(tool_call, RequiredFunctionToolCall):
            continue
        fcc = FunctionCallContent(
            id=tool_call.id,
            index=getattr(tool_call, "index", None),
            name=tool_call.function.name,
            arguments=tool_call.function.arguments,
        )
        function_call_contents.append(fcc)
        function_steps[tool_call.id] = fcc
    return function_call_contents


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


@experimental
def generate_function_result_content(
    agent_name: str, function_step: FunctionCallContent, tool_call: "RunStepFunctionToolCall"
) -> ChatMessageContent:
    """Generate function result content."""
    function_call_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.TOOL, name=agent_name)  # type: ignore
    function_call_content.items.append(
        FunctionResultContent(
            function_name=function_step.function_name,
            plugin_name=function_step.plugin_name,
            id=function_step.id,
            result=tool_call.function.get("output"),  # type: ignore
        )
    )
    return function_call_content


@experimental
def generate_bing_grounding_content(
    agent_name: str, bing_tool_call: "RunStepBingGroundingToolCall"
) -> ChatMessageContent:
    """Generate function result content related to a Bing Grounding Tool."""
    message_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.ASSISTANT, name=agent_name)  # type: ignore
    message_content.items.append(
        FunctionCallContent(
            id=bing_tool_call.id,
            name=bing_tool_call.type,
            function_name=bing_tool_call.type,
            arguments=bing_tool_call.bing_grounding,
        )
    )
    return message_content


@experimental
def generate_azure_ai_search_content(
    agent_name: str, azure_ai_search_tool_call: "RunStepAzureAISearchToolCall"
) -> ChatMessageContent:
    """Generate function result content related to an Azure AI Search Tool."""
    message_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.ASSISTANT, name=agent_name)  # type: ignore
    # Azure AI Search tool call contains both tool call input and output
    message_content.items.append(
        FunctionCallContent(
            id=azure_ai_search_tool_call.id,
            name=azure_ai_search_tool_call.type,
            function_name=azure_ai_search_tool_call.type,
            arguments=azure_ai_search_tool_call.azure_ai_search.get("input"),
        )
    )
    message_content.items.append(
        FunctionResultContent(
            function_name=azure_ai_search_tool_call.type,
            id=azure_ai_search_tool_call.id,
            result=azure_ai_search_tool_call.azure_ai_search.get("output"),
        )
    )
    return message_content


@experimental
def generate_file_search_content(
    agent_name: str, file_search_tool_call: "RunStepFileSearchToolCall"
) -> ChatMessageContent:
    """Generate function result content related to an Azure AI Search Tool."""
    message_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.ASSISTANT, name=agent_name)  # type: ignore
    # Azure AI Search tool call contains both tool call input and output
    message_content.items.append(
        FunctionCallContent(
            id=file_search_tool_call.id,
            name=file_search_tool_call.type,
            function_name=file_search_tool_call.type,
            arguments=file_search_tool_call.file_search.get("ranking_options", None),
        )
    )
    message_content.items.append(
        FunctionResultContent(
            function_name=file_search_tool_call.type,
            id=file_search_tool_call.id,
            result=file_search_tool_call.file_search.get("results", None),
        )
    )
    return message_content


@experimental
def generate_openapi_content(agent_name: str, openapi_tool_call: RunStepOpenAPIToolCall) -> ChatMessageContent:
    """Generate ChatMessageContent for a non-streaming OpenAPI tool call."""
    tool_id = openapi_tool_call.get("id")
    tool_type = openapi_tool_call.get("type", "openapi")
    function: dict[str, Any] = openapi_tool_call.get("function", {})

    items: list[FunctionCallContent | FunctionResultContent] = []

    arguments = function.get("arguments")
    if arguments:
        items.append(
            FunctionCallContent(
                id=tool_id,
                name=tool_type,
                function_name=function.get("name"),
                arguments=arguments,
            )
        )

    output = function.get("output")
    if output:
        items.append(
            FunctionResultContent(
                function_name=function.get("name"),
                id=tool_id,
                name=tool_type,
                result=output,
            )
        )

    return ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=items,  # type: ignore
        name=agent_name,
    )


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
    agent_name: str, step_details: "RunStepDeltaToolCallObject"
) -> "StreamingChatMessageContent | None":
    """Generate streaming function content.

    Args:
        agent_name: The agent name.
        step_details: The function step.

    Returns:
        StreamingChatMessageContent: The chat message content.
    """
    if not step_details.tool_calls:
        return None

    items: list[FunctionCallContent] = []

    tool_calls: list[
        RunStepDeltaCodeInterpreterToolCall | RunStepDeltaFileSearchToolCall | RunStepDeltaFunctionToolCall
    ] = cast(
        list[RunStepDeltaCodeInterpreterToolCall | RunStepDeltaFileSearchToolCall | RunStepDeltaFunctionToolCall],
        step_details.tool_calls or [],
    )

    for tool in tool_calls:
        if tool.type == "function" and tool.function:
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
def generate_streaming_bing_grounding_content(
    agent_name: str, step_details: "RunStepDeltaToolCallObject"
) -> StreamingChatMessageContent | None:
    """Generate StreamingChatMessageContent for Bing Grounding tool calls, filtering out empty results."""
    if not step_details.tool_calls:
        return None

    items: list[FunctionCallContent] = []
    for index, tool in enumerate(step_details.tool_calls):
        if tool.type != "bing_grounding":
            continue

        arguments = tool.get("bing_grounding", {}) or {}
        requesturl = arguments.get("requesturl", "")
        response_metadata = arguments.get("response_metadata", None)

        # Only skip if BOTH are missing/empty
        if requesturl == "" and response_metadata is None:
            continue

        items.append(
            FunctionCallContent(
                id=tool.id,
                index=index,
                name=tool.type,
                function_name=tool.type,
                arguments=arguments,
            )
        )

    if not items:
        return None

    return StreamingChatMessageContent(
        role=AuthorRole.ASSISTANT,
        name=agent_name,
        choice_index=0,
        items=items,  # type: ignore
    )


@experimental
def generate_streaming_azure_ai_search_content(
    agent_name: str, step_details: "RunStepDeltaToolCallObject"
) -> StreamingChatMessageContent | None:
    """Generate function result content related to a Bing Grounding Tool."""
    if not step_details.tool_calls:
        return None

    items: list[FunctionCallContent | FunctionResultContent] = []

    for index, tool in enumerate(step_details.tool_calls):
        if tool.type == "azure_ai_search":
            azure_ai_search_tool = cast(RunStepAzureAISearchToolCall, tool)
            arguments = getattr(azure_ai_search_tool, "azure_ai_search", None)
            items.append(
                FunctionCallContent(
                    id=azure_ai_search_tool.id,
                    index=index,
                    name=azure_ai_search_tool.type,
                    function_name=azure_ai_search_tool.type,
                    arguments=arguments,
                )
            )
            items.append(
                FunctionResultContent(
                    function_name=azure_ai_search_tool.type,
                    id=azure_ai_search_tool.id,
                    result=azure_ai_search_tool.azure_ai_search.get("output"),
                )
            )

    return StreamingChatMessageContent(
        role=AuthorRole.ASSISTANT,
        name=agent_name,
        choice_index=0,
        items=items,  # type: ignore
    )  # type: ignore


@experimental
def generate_streaming_file_search_content(
    agent_name: str, step_details: "RunStepDeltaToolCallObject"
) -> StreamingChatMessageContent | None:
    """Generate function result content related to a File Search Tool."""
    if not step_details.tool_calls:
        return None

    items: list[FunctionCallContent | FunctionResultContent] = []

    for index, tool in enumerate(step_details.tool_calls):
        if tool.type == "file_search":
            file_search_tool = cast(RunStepFileSearchToolCall, tool)
            arguments = getattr(file_search_tool, "file_search", None)
            results: list[Any] = []
            if arguments is not None:
                results = arguments.pop("results", None)
            items.append(
                FunctionCallContent(
                    id=file_search_tool.id,
                    index=index,
                    name=file_search_tool.type,
                    function_name=file_search_tool.type,
                    arguments=arguments,
                )
            )
            items.append(
                FunctionResultContent(
                    function_name=file_search_tool.type,
                    id=file_search_tool.id,
                    name=file_search_tool.type,
                    result=results,
                )
            )

    return StreamingChatMessageContent(
        role=AuthorRole.ASSISTANT,
        name=agent_name,
        choice_index=0,
        items=items,  # type: ignore
    )


@experimental
def generate_streaming_openapi_content(
    agent_name: str,
    step_details: "RunStepDeltaToolCallObject",
) -> "StreamingChatMessageContent | None":
    """Generate OpenAPI content for streaming function/tool call messages."""
    if not getattr(step_details, "tool_calls", None):
        return None

    items: list[FunctionCallContent | FunctionResultContent] = []  # type: ignore

    for index, tool in enumerate(step_details.tool_calls or []):
        if tool.get("type") != "openapi":
            continue

        func: dict[str, Any] = tool.get("function")
        tool_id = tool.get("id")
        arguments = func.get("arguments") if func else None
        if arguments:
            items.append(
                FunctionCallContent(
                    id=tool_id,
                    index=index,
                    name="openapi",
                    function_name=func.get("name") if func else None,
                    arguments=arguments,
                )
            )

        output = func.get("output") if func else None
        if output:
            items.append(
                FunctionResultContent(
                    function_name=func.get("name") if func else None,
                    id=tool_id,
                    name="openapi",
                    result=output,
                )
            )

    if not items:
        return None

    return StreamingChatMessageContent(
        role=AuthorRole.ASSISTANT,
        name=agent_name,
        choice_index=0,
        items=items,  # type: ignore
    )


@experimental
def generate_streaming_code_interpreter_content(
    agent_name: str, step_details: "RunStepDeltaToolCallObject"
) -> "StreamingChatMessageContent | None":
    """Generate code interpreter content.

    Args:
        agent_name: The agent name.
        step_details: The current step details.

    Returns:
        StreamingChatMessageContent: The chat message content.
    """
    items: list[StreamingTextContent | StreamingFileReferenceContent] = []

    if not step_details.tool_calls:
        return None

    metadata: dict[str, bool] = {}
    for index, tool in enumerate(step_details.tool_calls):
        if isinstance(tool, RunStepDeltaCodeInterpreterToolCall):
            code_interpreter_tool_call = tool.code_interpreter
            if code_interpreter_tool_call is None:
                continue
            if code_interpreter_tool_call.input:
                items.append(
                    StreamingTextContent(
                        choice_index=index,
                        text=code_interpreter_tool_call.input,
                    )
                )
                metadata["code"] = True
            if code_interpreter_tool_call.outputs:
                for output in code_interpreter_tool_call.outputs:
                    if (
                        isinstance(output, RunStepDeltaCodeInterpreterImageOutput)
                        and output.image is not None
                        and output.image.file_id
                    ):
                        items.append(
                            StreamingFileReferenceContent(
                                file_id=output.image.file_id,
                            )
                        )
                    if isinstance(output, RunStepDeltaCodeInterpreterLogOutput) and output.logs:
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
def generate_annotation_content(
    annotation: MessageTextFilePathAnnotation | MessageTextFileCitationAnnotation | MessageTextUrlCitationAnnotation,
) -> AnnotationContent:
    """Generate annotation content with safe attribute access."""
    file_id = None
    url = None
    title = None
    citation_type = None
    if isinstance(annotation, MessageTextFilePathAnnotation) and annotation.file_path:
        file_id = annotation.file_path.file_id
        citation_type = CitationType.FILE_PATH
    elif isinstance(annotation, MessageTextFileCitationAnnotation) and annotation.file_citation:
        file_id = annotation.file_citation.file_id
        citation_type = CitationType.FILE_CITATION
    elif isinstance(annotation, MessageTextUrlCitationAnnotation) and annotation.url_citation:
        url = annotation.url_citation.url
        title = annotation.url_citation.title
        citation_type = CitationType.URL_CITATION

    return AnnotationContent(
        file_id=file_id,
        quote=getattr(annotation, "text", None),
        start_index=getattr(annotation, "start_index", None),
        end_index=getattr(annotation, "end_index", None),
        url=url,
        title=title,
        citation_type=citation_type,
    )


@experimental
def generate_streaming_annotation_content(
    annotation: MessageDeltaTextFilePathAnnotation
    | MessageDeltaTextFileCitationAnnotation
    | MessageDeltaTextUrlCitationAnnotation,
) -> StreamingAnnotationContent:
    """Generate streaming annotation content with defensive checks."""
    file_id = None
    url = None
    quote = None
    title = None
    citation_type = None
    if isinstance(annotation, MessageDeltaTextFilePathAnnotation) and annotation.file_path:
        file_id = annotation.file_path.file_id
        quote = getattr(annotation, "text", None)
        citation_type = CitationType.FILE_PATH
    elif isinstance(annotation, MessageDeltaTextFileCitationAnnotation) and annotation.file_citation:
        file_id = annotation.file_citation.file_id
        quote = getattr(annotation, "text", None)
        citation_type = CitationType.FILE_CITATION
    elif isinstance(annotation, MessageDeltaTextUrlCitationAnnotation) and annotation.url_citation:
        url = annotation.url_citation.url
        title = annotation.url_citation.title
        quote = annotation.get("text", None)
        citation_type = CitationType.URL_CITATION

    return StreamingAnnotationContent(
        file_id=file_id,
        quote=quote,
        start_index=getattr(annotation, "start_index", None),
        end_index=getattr(annotation, "end_index", None),
        url=url,
        title=title,
        citation_type=citation_type,
    )
