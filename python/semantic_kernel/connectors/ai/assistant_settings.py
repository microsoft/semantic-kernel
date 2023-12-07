# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class OpenAIAssistantSettings(SKBaseModel):
    """Settings for creating an OpenAI assistant."""

    name: str = Field(min_length=1, max_length=256)
    description: Optional[str] = Field(max_length=512)
    instructions: Optional[str] = Field(max_length=32768)
