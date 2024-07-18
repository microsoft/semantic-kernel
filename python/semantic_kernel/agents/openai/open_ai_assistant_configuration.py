# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping
from datetime import timedelta

from openai import AsyncOpenAI
from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class PollingConfiguration(KernelBaseModel):
    """Configuration and defaults associated with polling behavior for Assistant API requests."""

    default_polling_interval: timedelta = Field(default=timedelta(milliseconds=500))
    default_polling_backoff: timedelta = Field(default=timedelta(seconds=1))
    default_message_synchronization_delay: timedelta = Field(default=timedelta(milliseconds=500))
    run_polling_interval: timedelta = Field(default=default_polling_interval)
    run_polling_backoff: timedelta = Field(default=default_polling_backoff)
    message_synchronization_delay: timedelta = Field(default=default_message_synchronization_delay)


class OpenAIAssistantConfiguration(KernelBaseModel):
    api_key: str | None = None
    org_id: str | None = None
    ai_model_id: str | None = None
    service_id: str | None = None
    endpoint: str | None = None
    version: str | None = None
    client: AsyncOpenAI | None = None
    default_headers: Mapping[str, str] | None = None
    polling: PollingConfiguration = Field(default_factory=PollingConfiguration)
    env_file_path: str | None = None
    env_file_encoding: str | None = None
