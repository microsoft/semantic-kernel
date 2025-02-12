# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, ClassVar, Literal, TypeAlias, Union

from pydantic import Field

from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

RealtimeEvent: TypeAlias = Annotated[
    Union[
        "RealtimeServiceEvent",
        "RealtimeAudioEvent",
        "RealtimeTextEvent",
        "RealtimeFunctionCallEvent",
        "RealtimeFunctionResultEvent",
        "RealtimeImageEvent",
    ],
    Field(discriminator="event_type"),
]


class RealtimeServiceEvent(KernelBaseModel):
    """Base class for all service events."""

    event: Any | None = Field(default=None, description="The event content.")
    service_type: str
    event_type: ClassVar[Literal["service"]] = "service"


class RealtimeAudioEvent(KernelBaseModel):
    """Audio event type."""

    audio: AudioContent = Field(..., description="Audio content.")
    service_type: str | None = None
    event_type: ClassVar[Literal["audio"]] = "audio"


class RealtimeTextEvent(KernelBaseModel):
    """Text event type."""

    text: TextContent = Field(..., description="Text content.")
    service_type: str | None = None
    event_type: ClassVar[Literal["text"]] = "text"


class RealtimeFunctionCallEvent(KernelBaseModel):
    """Function call event type."""

    function_call: FunctionCallContent = Field(..., description="Function call content.")
    service_type: str | None = None
    event_type: ClassVar[Literal["function_call"]] = "function_call"


class RealtimeFunctionResultEvent(KernelBaseModel):
    """Function result event type."""

    function_result: FunctionResultContent = Field(..., description="Function result content.")
    service_type: str | None = None
    event_type: ClassVar[Literal["function_result"]] = "function_result"


class RealtimeImageEvent(KernelBaseModel):
    """Image event type."""

    image: ImageContent = Field(..., description="Image content.")
    service_type: str | None = None
    event_type: ClassVar[Literal["image"]] = "image"
