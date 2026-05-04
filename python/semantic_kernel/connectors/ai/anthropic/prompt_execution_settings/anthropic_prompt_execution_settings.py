# Copyright (c) Microsoft. All rights reserved.

import copy
import logging
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError

logger = logging.getLogger(__name__)


class AnthropicCacheSettings(BaseModel):
    """Configuration for Anthropic prompt caching.

    Controls which parts of the request receive cache_control injection.

    Anthropic minimum token thresholds for cache activation:
      - claude-haiku-4-5 : 4,096 tokens
      - claude-sonnet-4-x: 1,024 tokens
      - claude-opus-4-x  : 1,024 tokens

    TTL options:
      - "5m": ephemeral 5-minute cache (1.25x write cost, 0.1x read cost)
      - "1h": extended 1-hour cache (2x write cost, 0.1x read cost)

    Use the classmethods for common configurations::

        AnthropicCacheSettings.on()  # enable system + tools caching
        AnthropicCacheSettings.off()  # disable all caching (default)
        AnthropicCacheSettings.system()  # cache system message only
        AnthropicCacheSettings.tools()  # cache tool definitions only
    """

    enabled: Annotated[
        bool,
        Field(description="Master switch — disabling skips all cache_control injection regardless of other flags."),
    ] = False
    cache_system: Annotated[
        bool,
        Field(description="Inject cache_control on the system message content block."),
    ] = False
    cache_tools: Annotated[
        bool,
        Field(description="Inject cache_control on the last tool definition, caching the entire tools array prefix."),
    ] = False
    ttl: Annotated[
        Literal["5m", "1h"],
        Field(description="Cache TTL. '5m' = 5-minute ephemeral (default). '1h' = 1-hour extended."),
    ] = "5m"

    def _cache_control(self) -> dict[str, Any]:
        """Return the cache_control block for the configured TTL."""
        if self.ttl == "1h":
            return {"type": "ephemeral", "ttl": 3600}
        return {"type": "ephemeral"}

    @classmethod
    def on(cls, ttl: Literal["5m", "1h"] = "5m") -> "AnthropicCacheSettings":
        """Enable caching for all supported request sections (system + tools)."""
        return cls(enabled=True, cache_system=True, cache_tools=True, ttl=ttl)

    @classmethod
    def off(cls) -> "AnthropicCacheSettings":
        """Disable all cache_control injection."""
        return cls(enabled=False)

    @classmethod
    def system(cls, ttl: Literal["5m", "1h"] = "5m") -> "AnthropicCacheSettings":
        """Enable caching for the system message only."""
        return cls(enabled=True, cache_system=True, cache_tools=False, ttl=ttl)

    @classmethod
    def tools(cls, ttl: Literal["5m", "1h"] = "5m") -> "AnthropicCacheSettings":
        """Enable caching for tool definitions only."""
        return cls(enabled=True, cache_system=False, cache_tools=True, ttl=ttl)

    @classmethod
    def short(cls) -> "AnthropicCacheSettings":
        """5-minute TTL. Use for tight agentic loops where the same prompt repeats within minutes.

        Write cost: 1.25x. Read cost: 0.1x. Breaks even after a single cache hit.
        """
        return cls(enabled=True, cache_system=True, cache_tools=True, ttl="5m")

    @classmethod
    def long(cls) -> "AnthropicCacheSettings":
        """1-hour TTL. Use for batch jobs or scheduled tasks with long gaps between calls.

        Write cost: 2x. Read cost: 0.1x. Needs at least 2 cache hits to break even.
        """
        return cls(enabled=True, cache_system=True, cache_tools=True, ttl="1h")


class AnthropicPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for Anthropic services."""

    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None


class AnthropicChatPromptExecutionSettings(AnthropicPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    messages: list[dict[str, Any]] | None = None
    stream: bool | None = None
    system: str | list[dict[str, Any]] | None = None
    max_tokens: Annotated[int, Field(gt=0)] = 1024
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    stop_sequences: list[str] | None = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    top_k: Annotated[int | None, Field(ge=0)] = None
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "Do not set this manually. It is set by the service based on the function choice configuration."
            ),
        ),
    ] = None
    tool_choice: Annotated[
        dict[str, str] | None,
        Field(
            description="Do not set this manually. It is set by the service based on the function choice configuration."
        ),
    ] = None
    cache: Annotated[
        AnthropicCacheSettings,
        Field(
            description="Prompt caching configuration. Disabled by default.",
            exclude=True,
        ),
    ] = Field(default_factory=AnthropicCacheSettings)

    @model_validator(mode="after")
    def validate_tool_choice(self) -> "AnthropicChatPromptExecutionSettings":
        """Validate tool choice. Anthropic doesn't support NONE tool choice."""
        tool_choice = self.tool_choice

        if tool_choice and tool_choice.get("type") == FunctionChoiceType.NONE.value:
            raise ServiceInvalidExecutionSettingsError("Tool choice 'none' is not supported by Anthropic.")

        return self

    def prepare_settings_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Prepare the settings dictionary, injecting cache_control blocks when caching is enabled."""
        data = super().prepare_settings_dict(**kwargs)

        if not self.cache.enabled:
            return data

        cache_control = self.cache._cache_control()

        if self.cache.cache_system:
            system = data.get("system")
            if isinstance(system, str) and system:
                data["system"] = [{"type": "text", "text": system, "cache_control": cache_control}]

        if self.cache.cache_tools:
            tools: list[dict[str, Any]] | None = data.get("tools")
            if tools:
                tools = copy.deepcopy(tools)
                tools[-1]["cache_control"] = cache_control
                data["tools"] = tools

        return data
