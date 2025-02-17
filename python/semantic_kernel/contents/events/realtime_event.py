# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, ClassVar, Literal, Union

from pydantic import Field

from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

RealtimeEvents = Annotated[
    Union[
        "RealtimeEvent",
        "RealtimeAudioEvent",
        "RealtimeTextEvent",
        "RealtimeFunctionCallEvent",
        "RealtimeFunctionResultEvent",
        "RealtimeImageEvent",
    ],
    Field(discriminator="event_type"),
]


class RealtimeEvent(KernelBaseModel):
    """Base class for all service events."""

    service_event: Any | None = Field(default=None, description="The event content.")
    service_type: str | None = None
    event_type: ClassVar[Literal["service"]] = "service"


class RealtimeAudioEvent(RealtimeEvent):
    """Audio event type."""

    event_type: ClassVar[Literal["audio"]] = "audio"  # type: ignore
    audio: AudioContent = Field(..., description="Audio content.")


class RealtimeTextEvent(RealtimeEvent):
    """Text event type."""

    event_type: ClassVar[Literal["text"]] = "text"  # type: ignore
    text: TextContent = Field(..., description="Text content.")


class RealtimeFunctionCallEvent(RealtimeEvent):
    """Function call event type."""

    event_type: ClassVar[Literal["function_call"]] = "function_call"  # type: ignore
    function_call: FunctionCallContent = Field(..., description="Function call content.")


class RealtimeFunctionResultEvent(RealtimeEvent):
    """Function result event type."""

    event_type: ClassVar[Literal["function_result"]] = "function_result"  # type: ignore
    function_result: FunctionResultContent = Field(..., description="Function result content.")


class RealtimeImageEvent(RealtimeEvent):
    """Image event type."""

    event_type: ClassVar[Literal["image"]] = "image"  # type: ignore
    image: ImageContent = Field(..., description="Image content.")
