# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from os import environ, path
from typing import TYPE_CHECKING, Any, ClassVar

from microsoft.agents.copilotstudio.client import CopilotClient
from microsoft.agents.core.models import Activity, ActivityTypes
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
    AgentInvokeException,
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


# ──────────────────────────────────────────────────────────────────────────────
# Thread abstraction
# ──────────────────────────────────────────────────────────────────────────────
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
        pre_buffer: list[Activity] | None = None,
    ) -> None:
        """Initializes a new instance of the CopilotStudioAgentThread class."""
        super().__init__()
        if client is None:
            raise ValueError("CopilotClient cannot be None")

        self._client = client
        self._id: str | None = conversation_id  # Copilot Studio conversation ID
        self._buffer: list[Activity] = pre_buffer or []  # Activities not yet flushed
        self._history: list[ChatMessageContent] = []

    # ——————————————————— life cycle ———————————————————
    @override
    async def _create(self) -> str:
        """Lazily starts a conversation **only when the first activity arrives**.

        Copilot Studio returns the conversation ID in the first `Activity`
        yielded by `start_conversation`.
        """
        return ""
        logger.debug("Starting Copilot Studio conversation …")
        async for activity in self._client.start_conversation():
            self._buffer.append(activity)
            # First 'event' activity always contains the ID
            if activity.conversation and activity.conversation.id:
                self._id = activity.conversation.id
                logger.debug("Conversation id = %s", self._id)
                break
        if not self._id:
            raise AgentThreadOperationException("Unable to fetch conversation ID from Copilot Studio")
        return self._id

    @override
    async def _delete(self) -> None:
        # Copilot Studio has no explicit delete endpoint; just drop state.
        self._buffer.clear()
        self._history.clear()

    # ——————————————————— message ingress hook ———————————————————
    @override
    async def _on_new_message(self, new_message: ChatMessageContent) -> None:
        """Called whenever SK adds a user/assistant message.

        We *do not* transmit
        outbound traffic here that happens in the agent's `get_response`.
        Instead we keep local history aligned with SK's Chat history reducer.
        """
        self._history.append(new_message)

    # ——————————————————— expose history to callers ———————————————————
    async def get_messages(self) -> AsyncIterable[ChatMessageContent]:
        """Returns the history of messages in the thread."""
        for msg in self._history:
            yield msg

    # Extra helper for agent
    async def _flush_buffer(self) -> list[ChatMessageContent]:
        """Convert buffered `Activity` objects to SK message content and clear buffer."""
        from semantic_kernel.contents.text_content import TextContent

        translated: list[ChatMessageContent] = []
        while self._buffer:
            act = self._buffer.pop(0)
            if act.type != ActivityTypes.message:
                continue  # ignore typing / event etc. for now
            translated.append(
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT
                    if act.from_property and act.from_property.role == "bot"
                    else AuthorRole.USER,
                    content=act.text,
                    metadata={
                        "activity_id": act.id,
                        "conversation_id": act.conversation.id if act.conversation else None,
                    },
                    items=[TextContent(text=act.text)],
                )
            )
        self._history.extend(translated)
        return translated


# ──────────────────────────────────────────────────────────────────────────────
# Agent proper
# ──────────────────────────────────────────────────────────────────────────────
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
    def acquire_token(mcs_settings: CopilotStudioAgentSettings, cache_path: str) -> str:
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
        token: str | None = None,
        app_client_id: str | None = None,
        tenant_id: str | None = None,
        environment_id: str | None = None,
        agent_identifier: str | None = None,
        cloud: str | None = None,
        copilot_agent_type: str | None = None,
        custom_power_platform_cloud: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> CopilotClient:
        """Set up the resources needed for the Copilot Studio agent."""
        try:
            connection_settings = CopilotStudioAgentSettings(
                app_client_id=app_client_id,
                tenant_id=tenant_id,
                environment_id=environment_id,
                agent_identifier=agent_identifier,
                cloud=cloud,
                copilot_agent_type=copilot_agent_type,
                custom_power_platform_cloud=custom_power_platform_cloud,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise AgentInitializationException(f"Failed to create Copilot Studio Agent settings: {exc}") from exc

        # if not connection_settings.app_client_id and not connection_settings.tenant_id:
        #     raise AgentInitializationException("The Copilot Studio Agent app client ID and tenant ID are required.")

        if not token:
            token = CopilotStudioAgent.acquire_token(
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
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Blocking single turn call   convenience for typical chat bots."""
        # Ensure we have a thread & propagate inbound user message(s)
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        assert isinstance(thread, CopilotStudioAgentThread)  # for typing

        # Take *only* the latest user message for now
        last_user_msg = thread._history[-1]
        user_text = last_user_msg.content or ""

        # Ask Copilot Studio
        logger.debug("Sending text to Copilot Studio: %s", user_text)
        # self.client.ask_question_with_activity()
        async for activity in self.client.ask_question(user_text):
            thread._buffer.append(activity)
        # Flush to ChatMessageContent
        replies = await thread._flush_buffer()
        if not replies:
            raise AgentInvokeException("Copilot Studio returned no assistant message.")
        final = replies[-1]
        await thread.on_new_message(final)
        return AgentResponseItem(message=final, thread=thread)

    # Streaming helpers.
    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Non streaming pipeline *with* intermediate assistant turns.

        We simply relay the activity stream and mark UX visible messages.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to call with each intermediate message.
            arguments: The arguments to pass to the agent.
            **kwargs: Additional keyword arguments.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        assert isinstance(thread, CopilotStudioAgentThread)

        # Forward last inbound user msg
        last_user_msg = thread._history[-1]
        async for activity in self.client.ask_question(last_user_msg.content or ""):
            thread._buffer.append(activity)
            flushed = await thread._flush_buffer()
            for msg in flushed:
                if on_intermediate_message:
                    await on_intermediate_message(msg)
                yield AgentResponseItem(message=msg, thread=thread)

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


# ──────────────────────────────────────────────────────────────────────────────
# Convenience factory (mirrors .setup_resources pattern in other agents)
# ──────────────────────────────────────────────────────────────────────────────
def setup_copilot_resources(client: CopilotClient | None = None, **kwargs) -> CopilotClient:
    """Very light helper allows symmetry with `setup_resources` used by other agents.

    You normally authenticate outside and just pass the client in.
    """
    if client:
        return client
    raise AgentInitializationException(
        "Copilot Studio requires an authenticated `CopilotClient`.  Pass one into `CopilotStudioAgent(client=...)`."
    )
