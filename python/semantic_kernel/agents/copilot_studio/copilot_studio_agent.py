# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from os import environ, path
from typing import TYPE_CHECKING, Any, ClassVar

from microsoft.agents.copilotstudio.client import (
    AgentType,
    CopilotClient,
    PowerPlatformCloud,
)
from microsoft.agents.core.models import ActivityTypes
from msal import PublicClientApplication
from msal_extensions import (
    FilePersistence,
    PersistedTokenCache,
    build_encrypted_persistence,
)
from pydantic import Field, ValidationError, model_validator

from semantic_kernel.agents import Agent
from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.copilot_studio.copilot_studio_agent_settings import CopilotStudioAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentInitializationException,
    AgentThreadOperationException,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.naming import generate_random_ascii_name

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import override

if TYPE_CHECKING:  # pragma: no cover
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class CopilotStudioAgentThread(AgentThread):
    """Wrapper around Copilot Studio conversation.

    A `CopilotClient` instance *owns* the websocket and caches the
    conversation ID internally; we only need to keep a handle to it so that
    messages written through Semantic Kernel land in the same session.
    """

    def __init__(
        self,
        client: CopilotClient,
        conversation_id: str | None = None,
    ) -> None:
        """Initializes a new instance of the CopilotStudioAgentThread class."""
        super().__init__()
        if client is None:
            raise ValueError("CopilotClient cannot be None")

        self._client = client
        self._conversation_id: str | None = conversation_id  # Copilot Studio conversation ID

    @property
    def conversation_id(self) -> str | None:
        """Get the conversation ID."""
        return self._conversation_id

    @conversation_id.setter
    def conversation_id(self, value: str | None) -> None:
        """Set the conversation ID."""
        self._conversation_id = value

    @override
    @property
    def id(self) -> str | None:
        """Get the thread ID."""
        return self.conversation_id

    # ——————————————————— life cycle ———————————————————
    @override
    async def _create(self) -> str:
        if self._is_deleted:
            raise AgentThreadOperationException(
                "Cannot create a new thread, since the current thread has been deleted."
            )
        return ""

    @override
    async def _delete(self) -> None:
        if self._is_deleted:
            return
        if self.conversation_id is None:
            raise AgentThreadOperationException("Cannot delete the thread, since it has not been created.")
        self._is_deleted = True

    # ——————————————————— message ingress hook ———————————————————
    @override
    async def _on_new_message(self, new_message: ChatMessageContent) -> None:
        pass

    # ——————————————————— expose history to callers ———————————————————
    async def get_messages(self) -> AsyncIterable[ChatMessageContent]:
        """Returns the history of messages in the thread."""
        for msg in self._history:
            yield msg


@experimental
class CopilotStudioAgent(Agent):
    """Semantic Kernel facade over Copilot Studio.

    Notes:
    > • Copilot Studio is fundamentally *event / activity* based rather than
    >   message based.  We translate activities ↔ ChatMessageContent at the edge.
    > • The client already implements auto reconnect & auth refresh; the agent
    >   therefore stays thin and stateless apart from conversation ID.
    """

    client: CopilotClient
    channel_type: ClassVar[type[AgentChannel]] = None
    # Copilot Studio has no concept of “tools” yet, but we keep the field for symmetry
    plugins: list[Any] = Field(default_factory=list)

    # ——————————————————— ctor ———————————————————
    def __init__(
        self,
        *,
        client: CopilotClient,
        arguments: KernelArguments | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        name: str | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
    ) -> None:
        """Initializes a new instance of the CopilotStudioAgent class."""
        args: dict[str, Any] = {
            "client": client,
            "name": name or f"copilot_agent_{generate_random_ascii_name(6)}",
            "description": description,
        }
        if id is not None:
            args["id"] = id
        if instructions is not None:
            args["instructions"] = instructions
        if kernel is not None:
            args["kernel"] = kernel
        if arguments is not None:
            args["arguments"] = arguments
        if plugins is not None:
            args["plugins"] = plugins

        if instructions and prompt_template_config and instructions != prompt_template_config.template:
            logger.info(
                "Both `instructions` and `prompt_template_config` supplied   "
                "using the template inside `prompt_template_config`."
            )

        if prompt_template_config:
            args["prompt_template"] = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )
            # Overrides raw instructions if template contains the final string
            if prompt_template_config.template:
                args["instructions"] = prompt_template_config.template

        super().__init__(**args)

    # Pydantic hook   make sure the CopilotClient has an active connection
    @model_validator(mode="after")
    def _check_client_connection(self) -> "CopilotStudioAgent":
        if not hasattr(self.client, "start_conversation"):
            raise AgentInitializationException(
                "client must be an instance of microsoft.agents.copilotstudio.CopilotClient"
            )
        return self

    # ——————————————————— high level API ———————————————————
    @staticmethod
    def get_msal_token_cache(cache_path: str, fallback_to_plaintext=True) -> PersistedTokenCache:
        """Get the MSAL token cache."""
        persistence = None

        # Note: This sample stores both encrypted persistence and plaintext persistence
        # into same location, therefore their data would likely override with each other.
        try:
            persistence = build_encrypted_persistence(cache_path)
        except:  # pylint: disable=bare-except
            # On Linux, encryption exception will be raised during initialization.
            # On Windows and macOS, they won't be detected here,
            # but will be raised during their load() or save().
            if not fallback_to_plaintext:
                raise
            logging.warning("Encryption unavailable. Opting in to plain text.")
            persistence = FilePersistence(cache_path)

        return PersistedTokenCache(persistence)

    @staticmethod
    def _acquire_token(mcs_settings: CopilotStudioAgentSettings, cache_path: str) -> str:
        cache = CopilotStudioAgent.get_msal_token_cache(cache_path)
        app = PublicClientApplication(
            mcs_settings.app_client_id,
            authority=f"https://login.microsoftonline.com/{mcs_settings.tenant_id}",
            token_cache=cache,
        )

        token_scopes = ["https://api.powerplatform.com/.default"]

        accounts = app.get_accounts()

        if accounts:
            # If so, you could then somehow display these accounts and let end user choose
            chosen = accounts[0]
            result = app.acquire_token_silent(scopes=token_scopes, account=chosen)
        else:
            # At this point, you can save you can update your cache if you are using token caching
            # check result variable, if its None then you should interactively acquire a token
            # So no suitable token exists in cache. Let's get a new one from Microsoft Entra.
            result = app.acquire_token_interactive(scopes=token_scopes)

        if "access_token" in result:
            return result["access_token"]
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug
        raise Exception("Authentication with the Public Application failed")

    @staticmethod
    def setup_resources(
        app_client_id: str | None = None,
        tenant_id: str | None = None,
        environment_id: str | None = None,
        agent_identifier: str | None = None,
        cloud: PowerPlatformCloud | None = None,
        copilot_agent_type: AgentType | None = None,
        custom_power_platform_cloud: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> CopilotClient:
        """Set up the resources needed for the Copilot Studio agent.

        Args:
            app_client_id: The app client ID. This is the app ID of the app registration configured in Entra.
            tenant_id: The tenant ID. This is the tenant ID related to the app registration.
            environment_id: The environment ID. This is from the Copilot Studio Advanced Metadata settings.
            agent_identifier: The agent identifier. This is the `Schema Name` of the agent from the
                Copilot Studio Advanced Metadata settings.
            cloud: The cloud environment.
            copilot_agent_type: The type of Copilot agent.
            custom_power_platform_cloud: The custom Power Platform cloud.
            env_file_path: The path to the environment file.
            env_file_encoding: The encoding of the environment file.

        Returns:
            CopilotClient: The Copilot client.
        """
        try:
            connection_settings = CopilotStudioAgentSettings(
                app_client_id=app_client_id,
                tenant_id=tenant_id,
                environment_id=environment_id,
                agent_identifier=agent_identifier,
                cloud=cloud,
                type=copilot_agent_type,
                custom_power_platform_cloud=custom_power_platform_cloud,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise AgentInitializationException(f"Failed to create Copilot Studio Agent settings: {exc}") from exc

        if not connection_settings.app_client_id and not connection_settings.tenant_id:
            raise AgentInitializationException("The Copilot Studio Agent app client ID and tenant ID are required.")

        token = CopilotStudioAgent._acquire_token(
            connection_settings,
            environ.get("TOKEN_CACHE_PATH") or path.join(path.dirname(__file__), "bin/token_cache.bin"),
        )
        return CopilotClient(connection_settings, token)

    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Blocking single turn call convenience for typical chat bots."""
        # Ensure we have a thread & propagate inbound user message(s)
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        assert isinstance(thread, CopilotStudioAgentThread)  # for typing

        responses: list[ChatMessageContent] = []
        async for response in self._inner_invoke(
            thread=thread,
            messages=messages,
            on_intermediate_message=None,
            arguments=arguments,
            kernel=kernel,
            **kwargs,
        ):
            responses.append(response)

        return AgentResponseItem(message=responses[-1], thread=thread)

    # Streaming helpers.
    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Non streaming pipeline *with* intermediate assistant turns.

        We simply relay the activity stream and mark UX visible messages.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to call with each intermediate message.
            arguments: The arguments to pass to the agent.
            kernel: The kernel to use for the agent.
            **kwargs: Additional keyword arguments.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        assert isinstance(thread, CopilotStudioAgentThread)

        async for response in self._inner_invoke(
            thread=thread,
            messages=messages,
            on_intermediate_message=on_intermediate_message,
            arguments=arguments,
            kernel=kernel,
            **kwargs,
        ):
            yield AgentResponseItem(message=response, thread=thread)

    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """True token level streaming is not yet exposed by Copilot Studio.

        We can still surface **chunked** assistant messages as they arrive.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        assert isinstance(thread, CopilotStudioAgentThread)

        last_user_msg = thread._history[-1]
        # ask_question() already yields incremental activities
        async for activity in self.client.ask_question(last_user_msg.content or ""):
            if activity.type != ActivityTypes.message:
                continue
            from semantic_kernel.contents.streaming_text_content import StreamingTextContent

            stream_msg = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                items=[StreamingTextContent(text=activity.text)],
                choice_index=0,
            )
            if on_intermediate_message:
                await on_intermediate_message(stream_msg)
            yield AgentResponseItem(message=stream_msg, thread=thread)

    async def _inner_invoke(
        self,
        thread: CopilotStudioAgentThread,
        messages: list[str] | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        messages_to_send = []
        formatted_instructions = await self.format_instructions(kernel, arguments)
        if formatted_instructions:
            messages_to_send.append(formatted_instructions)

        if not thread.id:
            async for activity in self.client.start_conversation():
                if not activity:
                    raise Exception("ChatConsoleService.start_service: Activity is None")
                if activity.type == ActivityTypes.message:
                    thread.conversation_id = activity.conversation.id

        async for activity in self.client.ask_question(messages, thread.id):
            if activity.type == ActivityTypes.message:
                if (
                    activity.text_format == "markdown"
                    and activity.suggested_actions
                    and activity.suggested_actions.actions
                ):
                    for action in activity.suggested_actions.actions:
                        if on_intermediate_message:
                            await on_intermediate_message(
                                ChatMessageContent(role=AuthorRole.ASSISTANT, content=action.text)
                            )
                yield ChatMessageContent(role=AuthorRole.ASSISTANT, content=activity.text)
