# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable, Awaitable, Callable
from copy import copy
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar

from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.beta.assistant import Assistant
from pydantic import Field, ValidationError, model_validator

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel
from semantic_kernel.agents.open_ai.assistant_thread_actions import AssistantThreadActions
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.kernel_pydantic import HttpsUrl
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import trace_agent_invocation
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from openai.types.beta.assistant_response_format_option_param import AssistantResponseFormatOptionParam
    from openai.types.beta.assistant_tool_param import AssistantToolParam
    from openai.types.beta.threads.message import Message
    from openai.types.beta.threads.run_create_params import TruncationStrategy

    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

_T = TypeVar("_T", bound="OpenAIAssistantAgent")

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIAssistantAgent(Agent):
    """OpenAI Assistant Agent class.

    Provides the ability to interact with OpenAI Assistants.
    """

    # region Agent Initialization
    client: AsyncOpenAI
    definition: Assistant
    plugins: list[Any] = Field(default_factory=list)
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)

    channel_type: ClassVar[type[AgentChannel]] = OpenAIAssistantChannel  # type: ignore

    def __init__(
        self,
        *,
        arguments: "KernelArguments | None" = None,
        client: AsyncOpenAI,
        definition: Assistant,
        kernel: "Kernel | None" = None,
        plugins: Any | None = None,
        polling_options: RunPollingOptions | None = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIAssistant service.

        Args:
            client: The OpenAI client.
            definition: The assistant definition.
            kernel: The Kernel instance.
            arguments: The arguments to pass to the function.
            prompt_template_config: The prompt template configuration.
            run_polling_options: The run polling options.
            kwargs: Additional keyword arguments.
        """
        args: dict[str, Any] = {
            "client": client,
            "definition": definition,
            "name": definition.name or f"azure_agent_{generate_random_ascii_name(length=8)}",
            "description": definition.description,
        }

        if arguments is not None:
            args["arguments"] = arguments
        if definition.id is not None:
            args["id"] = definition.id
        if definition.instructions is not None:
            args["instructions"] = definition.instructions
        if kernel is not None:
            args["kernel"] = kernel

        if (
            definition.instructions
            and prompt_template_config
            and definition.instructions != prompt_template_config.template
        ):
            logger.info(
                f"Both `instructions` ({definition.instructions}) and `prompt_template_config` "
                f"({prompt_template_config.template}) were provided. Using template in `prompt_template_config` "
                "and ignoring `instructions`."
            )

        if plugins is not None:
            args["plugins"] = plugins

        if prompt_template_config is not None:
            args["prompt_template"] = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )
            if prompt_template_config.template is not None:
                # Use the template from the prompt_template_config if it is provided
                args["instructions"] = prompt_template_config.template
        if polling_options is not None:
            args["polling_options"] = polling_options
        if kwargs:
            args.update(kwargs)
        super().__init__(**args)

    @model_validator(mode="after")
    def configure_kernel(self) -> None:
        """Configure the kernel."""
        if self.plugins:
            # Note, plugins provided via the constructor take precedence over those already in the kernel
            for plugin in self.plugins:
                self.kernel.add_plugins(plugin)

    @classmethod
    def create_openai_client(
        cls: type[_T],
        *,
        api_key: str | None = None,
        org_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        default_headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncOpenAI:
        """An internal method to create the OpenAI client from the provided arguments.

        Args:
            api_key: The API key.
            org_id: The organization ID.
            env_file_path: The environment file path.
            env_file_encoding: The environment file encoding.
            default_headers: The default headers.
            kwargs: Additional keyword arguments.

        Returns:
            An OpenAI client instance.
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationException("Failed to create OpenAI settings.", ex) from ex

        if not openai_settings.api_key:
            raise AgentInitializationException("The OpenAI API key is required.")

        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if default_headers:
            merged_headers.update(default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        return AsyncOpenAI(
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            organization=openai_settings.org_id,
            default_headers=merged_headers,
            **kwargs,
        )

    @classmethod
    def create_azure_openai_client(
        cls: type[_T],
        *,
        ad_token: str | None = None,
        ad_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        token_scope: str | None = None,
        **kwargs: Any,
    ) -> AsyncAzureOpenAI:
        """An internal method to create the OpenAI client from the provided arguments.

        Args:
            ad_token: The Azure AD token.
            ad_token_provider: The Azure AD token provider.
            api_key: The API key
            api_version: The API version.
            base_url: The base URL in the form https://<resource>.azure.openai.com/openai/deployments/<deployment_name>
            default_headers: The default headers.
            deployment_name: The deployment name.
            endpoint: The endpoint in the form https://<resource>.azure.openai.com
            env_file_path: The environment file path.
            env_file_encoding: The environment file encoding.
            token_scope: The token scope.
            kwargs: Additional keyword arguments.

        Returns:
            An OpenAI client instance.
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                chat_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_scope,
            )
        except ValidationError as exc:
            raise AgentInitializationException(f"Failed to create Azure OpenAI settings: {exc}") from exc

        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if default_headers:
            merged_headers.update(default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not azure_openai_settings.base_url:
            if not azure_openai_settings.endpoint:
                raise AgentInitializationException("Please provide an endpoint or a base_url")
            azure_openai_settings.base_url = HttpsUrl(  # type: ignore
                f"{str(azure_openai_settings.endpoint).rstrip('/')}/openai/deployments/{azure_openai_settings.chat_deployment_name}"
            )
        return AsyncAzureOpenAI(
            base_url=str(azure_openai_settings.base_url),
            api_version=azure_openai_settings.api_version,
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            azure_ad_token=ad_token,
            azure_ad_token_provider=ad_token_provider,
            default_headers=merged_headers,
            **kwargs,
        )

    # endregion

    # region Message Handling

    async def add_chat_message(
        self, thread_id: str, message: "str | ChatMessageContent", **kwargs: Any
    ) -> "Message | None":
        """Add a chat message to the thread.

        Args:
            thread_id: The ID of the thread
            message: The chat message to add
            kwargs: Additional keyword arguments

        Returns:
            The thread message or None
        """
        return await AssistantThreadActions.create_message(
            client=self.client, thread_id=thread_id, message=message, **kwargs
        )

    # endregion

    # region Invocation Methods

    @trace_agent_invocation
    async def invoke(
        self,
        thread_id: str,
        *,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        instructions_override: str | None = None,
        additional_instructions: str | None = None,
        additional_messages: "list[ChatMessageContent] | None" = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent.

        Args:
            thread_id: The ID of the thread.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: Parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            kwargs: Additional keyword arguments.

        Yields:
            The chat message content.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        run_level_params = {
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning_effort": reasoning_effort,
            "response_format": response_format,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation_strategy": truncation_strategy,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        async for is_visible, message in AssistantThreadActions.invoke(
            agent=self,
            thread_id=thread_id,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,
        ):
            if is_visible:
                yield message

    @trace_agent_invocation
    async def invoke_stream(
        self,
        thread_id: str,
        *,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        instructions_override: str | None = None,
        additional_instructions: str | None = None,
        additional_messages: "list[ChatMessageContent] | None" = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        messages: "list[ChatMessageContent] | None" = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent.

        Args:
            thread_id: The ID of the thread.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            messages: The messages that act as a receiver for completed messages.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: Parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            kwargs: Additional keyword arguments.

        Yields:
            The chat message content.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        run_level_params = {
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning_effort": reasoning_effort,
            "response_format": response_format,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation_strategy": truncation_strategy,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        async for message in AssistantThreadActions.invoke_stream(
            agent=self,
            thread_id=thread_id,
            kernel=kernel,
            arguments=arguments,
            messages=messages,
            **run_level_params,
        ):
            yield message

    # endregion
