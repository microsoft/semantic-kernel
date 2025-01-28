# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, Literal, TypeAlias, Union

from pydantic import Field

from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

RealtimeEvent: TypeAlias = Annotated[
    Union["ServiceEvent", "AudioEvent", "TextEvent", "FunctionCallEvent", "FunctionResultEvent"],
    Field(discriminator="event_type"),
]


class ServiceEvent(KernelBaseModel):
    """Base class for all service events."""

    event_type: Literal["service"]
    service_type: str
    event: Any | None = None


class AudioEvent(KernelBaseModel):
    """Audio event type."""

    event_type: Literal["audio"]
    service_type: str | None = None
    audio: AudioContent


class TextEvent(KernelBaseModel):
    """Text event type."""

    event_type: Literal["text"]
    service_type: str | None = None
    text: TextContent


class FunctionCallEvent(KernelBaseModel):
    """Function call event type."""

    event_type: Literal["function_call"]
    service_type: str | None = None
    function_call: FunctionCallContent


class FunctionResultEvent(KernelBaseModel):
    """Function result event type."""

    event_type: Literal["function_result"]
    service_type: str | None = None
    function_result: FunctionResultContent
