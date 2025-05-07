# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Awaitable, Callable, Sequence
from os import environ, path
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from microsoft.agents.copilotstudio.client import (
    AgentType,
    CopilotClient,
    PowerPlatformCloud,
)
from microsoft.agents.core.models import ActivityTypes
from msal import (
    ConfidentialClientApplication,
    PublicClientApplication,
)
from msal_extensions import (
    FilePersistence,
    PersistedTokenCache,
    build_encrypted_persistence,
)
from pydantic import ValidationError

from semantic_kernel.agents import Agent
from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.copilot_studio.copilot_studio_agent_settings import (
    CopilotStudioAgentAuthMode,
    CopilotStudioAgentSettings,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentInitializationException,
    AgentThreadInitializationException,
    AgentThreadOperationException,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import override

if TYPE_CHECKING:  # pragma: no cover
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


# region Token Factory


@experimental
def _log_auth_failure(result: dict[str, Any]) -> None:
    category = result.get("error", "unknown_error")
    corr_id = result.get("correlation_id", "n/a")[:8]  # Only log the first 8 characters
    logger.error(f"Copilot auth failure, category={category}, corr_id={corr_id}")


@experimental
class _CopilotStudioAgentTokenFactory:
    """A CopilotStudioAgentTokenFactory to handle authentication for the Copilot Studio agent."""

    def __init__(
        self,
        *,
        settings: CopilotStudioAgentSettings,
        cache_path: str,
        mode: CopilotStudioAgentAuthMode,
        client_secret: str | None = None,
        client_certificate: Path | None = None,
        user_assertion: str | None = None,
        scopes: Sequence[str] | None = None,
    ) -> None:
        self.settings = settings
        self.cache = self._get_msal_token_cache(cache_path)
        self.mode = mode
        self.client_secret = client_secret
        self.client_cert_path = client_certificate
        self.user_assertion = user_assertion
        self.scopes = scopes or ["https://api.powerplatform.com/.default"]

    @staticmethod
    def _get_msal_token_cache(cache_path: str, fallback_to_plaintext=True) -> PersistedTokenCache:
        """Get the MSAL token cache."""
        persistence = None

        # Note: This stores both encrypted persistence and plaintext persistence
        # into same location, therefore their data would likely override with each other.
        try:
            persistence = build_encrypted_persistence(cache_path)
        except Exception:  # pylint: disable=bare-except
            # On Linux, encryption exception will be raised during initialization.
            # On Windows and macOS, they won't be detected here,
            # but will be raised during their load() or save().
            if not fallback_to_plaintext:
                raise
            logging.warning("Encryption unavailable. Opting in to plain text.")
            persistence = FilePersistence(cache_path)

        return PersistedTokenCache(persistence)

    def acquire(self) -> str:
        """Return a valid bearer token or raise AgentInitializationException."""
        if self.mode is CopilotStudioAgentAuthMode.SERVICE:
            # SERVICE auth wiring is present but not yet supported end-to-end.
            logger.warning("SERVICE authentication mode is not yet supported; falling back to error.")
            raise AgentInitializationException(
                "Copilot Studio SERVICE authentication is not available yet. Please use INTERACTIVE mode instead."
            )

        match self.mode:
            case CopilotStudioAgentAuthMode.SERVICE:
                return self._acquire_service_token()  # unreachable until the guard is removed
            case _:
                return self._acquire_interactive_token()

    def _new_confidential_client(self, **extra_kwargs) -> ConfidentialClientApplication:
        return ConfidentialClientApplication(
            client_id=self.settings.app_client_id,
            authority=f"https://login.microsoftonline.com/{self.settings.tenant_id}",
            token_cache=self.cache,
            **extra_kwargs,
        )

    def _acquire_service_token(self) -> str:
        if not self.client_secret and not self.client_cert_path:
            raise AgentInitializationException(
                "client_secret *or* client_certificate is required for service-to-service auth."
            )

        kwargs: dict[str, Any] = {}
        if self.client_secret:
            kwargs["client_credential"] = self.client_secret
        else:  # certificate
            if not self.client_cert_path:
                raise AgentInitializationException(
                    "If no client_secret is provided, a client_certificate is required for service-to-service auth."
                )
            kwargs["client_credential"] = {
                "private_key": Path(self.client_cert_path).read_text(),
                "thumbprint": self._cert_thumbprint(self.client_cert_path),
            }

        app = self._new_confidential_client(**kwargs)

        # proactive caching
        result = app.acquire_token_silent(self.scopes, account=None) or app.acquire_token_for_client(scopes=self.scopes)

        return self._unwrap(result)

    # interactive
    def _acquire_interactive_token(self) -> str:
        app = PublicClientApplication(
            self.settings.app_client_id,
            authority=f"https://login.microsoftonline.com/{self.settings.tenant_id}",
            token_cache=self.cache,
        )
        accounts = app.get_accounts()
        result = (
            app.acquire_token_silent(self.scopes, account=accounts[0])
            if accounts
            else app.acquire_token_interactive(self.scopes)
        )
        return self._unwrap(result)

    @staticmethod
    def _unwrap(result: dict[str, Any]) -> str:
        if "access_token" in result:
            return result["access_token"]
        _log_auth_failure(result)
        raise AgentInitializationException("Authentication failed; see logs for category and correlation code.")

    @staticmethod
    def _cert_thumbprint(cert_path: Path) -> str:
        import hashlib
        import ssl

        pem_bytes = Path(cert_path).read_bytes()
        der_bytes = ssl.PEM_cert_to_DER_cert(pem_bytes.decode())
        return hashlib.sha1(der_bytes, usedforsecurity=False).hexdigest().upper()


# endregion


# region CopilotStudioAgentThread


@experimental
class CopilotStudioAgentThread(AgentThread):
    """The Copilot Studio Agent Thread."""

    def __init__(
        self,
        client: CopilotClient,
        conversation_id: str | None = None,
    ) -> None:
        """Initializes a new instance of the CopilotStudioAgentThread class.

        Args:
            client: The Copilot Client.
            conversation_id: The conversation ID. This is the Copilot Studio conversation ID.
        """
        super().__init__()
        if client is None:
            raise AgentThreadInitializationException("CopilotClient cannot be None")

        self._client = client
        self._conversation_id = conversation_id  # Copilot Studio conversation ID

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

    @override
    async def _create(self) -> str:
        # Creation is deferred to CopilotStudioAgent._ensure_conversation.
        if self._is_deleted:
            raise AgentThreadOperationException("Cannot create a thread that has been deleted.")
        return ""

    @override
    async def _delete(self) -> None:
        if self._is_deleted:
            return
        if self.conversation_id is None:
            raise AgentThreadOperationException("Cannot delete the thread, since it has not been created.")
        self._conversation_id = None
        self._is_deleted = True

    @override
    async def _on_new_message(self, new_message: ChatMessageContent) -> None:
        raise NotImplementedError(
            "This method is not implemented for CopilotStudioAgent. "
            "Messages and responses are automatically handled by the Copilot Agent."
        )


@experimental
class CopilotStudioAgent(Agent):
    """Semantic Kernel abstraction over a Copilot Studio Agent."""

    client: CopilotClient
    channel_type: ClassVar[type[AgentChannel] | None] = None

    def __init__(
        self,
        *,
        client: CopilotClient | None = None,
        arguments: KernelArguments | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        name: str | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
    ) -> None:
        """Initializes a new instance of the CopilotStudioAgent class.

        Args:
            client: The Copilot Client
            arguments: The Kernel Arguments to use at the agent-level.
            description: The description of the agent.
            id: The unique identifier for the agent. If not provided,
                a unique GUID will be generated.
            instructions: The instructions for the agent.
            kernel: The kernel instance.
            name: The name of the agent.
            prompt_template_config: The prompt template configuration for the agent.
        """
        if client is None:
            client = self.create_client()

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

    def model_post_init(self, __ctx: Any) -> None:
        """Post-initialization hook for the model."""
        super().model_post_init(__ctx)
        if self.kernel.plugins:
            logger.warning("Plugins are not supported by CopilotStudioAgent; any kernel plugins will be ignored.")

    @staticmethod
    def create_client(
        *,
        auth_mode: CopilotStudioAgentAuthMode | Literal["interactive", "service"] | None = None,
        agent_identifier: str | None = None,
        app_client_id: str | None = None,
        client_secret: str | None = None,
        client_certificate: str | None = None,
        cloud: PowerPlatformCloud | None = None,
        copilot_agent_type: AgentType | None = None,
        custom_power_platform_cloud: str | None = None,
        env_file_encoding: str | None = None,
        env_file_path: str | None = None,
        environment_id: str | None = None,
        tenant_id: str | None = None,
        user_assertion: str | None = None,
    ) -> CopilotClient:
        """Create the Copilot Studio Agent Client.

        Args:
            auth_mode: The authentication mode. This can be either `interactive` or `service`.
            agent_identifier: The agent identifier. This is the `Schema Name` of the agent from the
                Copilot Studio Advanced Metadata settings.
            app_client_id: The app client ID. This is the app ID of the app registration configured in Entra.
            client_secret: The client secret. This is the secret of the app registration.
            client_certificate: The client certificate. This is the certificate of the app registration.
            cloud: The cloud environment.
            copilot_agent_type: The type of Copilot agent.
            custom_power_platform_cloud: The custom Power Platform cloud.
            env_file_path: The path to the environment file.
            env_file_encoding: The encoding of the environment file.
            environment_id: The environment ID. This is from the Copilot Studio Advanced Metadata settings.
            tenant_id: The tenant ID. This is the tenant ID related to the app registration.
            user_assertion: The user assertion. This is the token used for on-behalf-of authentication.

        Returns:
            CopilotClient: The Copilot client.
        """
        if auth_mode is not None and isinstance(auth_mode, str):
            auth_mode = CopilotStudioAgentAuthMode(auth_mode)

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
                client_secret=client_secret,
                client_certificate=client_certificate,
                user_assertion=user_assertion,
                auth_mode=auth_mode,
            )
        except ValidationError as exc:
            raise AgentInitializationException(f"Failed to create Copilot Studio Agent settings: {exc}") from exc

        missing_params = [name for name in ("app_client_id", "tenant_id") if not getattr(connection_settings, name)]
        if missing_params:
            raise AgentInitializationException(f"Missing required configuration field(s): {', '.join(missing_params)}")

        cache_file = environ.get("TOKEN_CACHE_PATH_INTERACTIVE") or path.join(
            path.dirname(__file__), "bin", "token_cache_interactive.bin"
        )

        token = _CopilotStudioAgentTokenFactory(
            settings=connection_settings,
            cache_path=cache_file,
            mode=connection_settings.auth_mode,
            client_secret=connection_settings.client_secret.get_secret_value()
            if connection_settings.client_secret
            else None,
            client_certificate=Path(client_certificate) if client_certificate else None,
            user_assertion=user_assertion,
        ).acquire()

        return CopilotClient(connection_settings, token)

    # region Invocation Methods

    @trace_agent_get_response
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
        """Get a response from the agent.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            arguments: The arguments to pass to the agent. These take precedence over the agent-defined args.
            kernel: The kernel to use for the agent. This kernel takes precedence over the agent-defined kernel.
            **kwargs: Additional keyword arguments.

        Returns:
            A chat message content and thread with the response.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        if not isinstance(thread, CopilotStudioAgentThread):
            raise AgentThreadOperationException("The thread is not a Copilot Studio Agent thread.")

        normalized_messages = self._normalize_messages(messages)

        responses: list[ChatMessageContent] = []
        async for response in self._inner_invoke(
            thread=thread,
            messages=normalized_messages,
            on_intermediate_message=None,
            arguments=arguments,
            kernel=kernel,
            **kwargs,
        ):
            responses.append(response)

        return AgentResponseItem(message=responses[-1], thread=thread)

    @trace_agent_invocation
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
        """Invoke the agent.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to call with each intermediate message.
            arguments: The arguments to pass to the agent.
            kernel: The kernel to use for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            A chat message content and thread with the response.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotStudioAgentThread(self.client),
            expected_type=CopilotStudioAgentThread,
        )
        if not isinstance(thread, CopilotStudioAgentThread):
            raise AgentThreadOperationException("The thread is not a Copilot Studio Agent thread.")

        normalized_messages = self._normalize_messages(messages)

        async for response in self._inner_invoke(
            thread=thread,
            messages=normalized_messages,
            on_intermediate_message=on_intermediate_message,
            arguments=arguments,
            kernel=kernel,
            **kwargs,
        ):
            yield AgentResponseItem(message=response, thread=thread)

    @override
    def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem["StreamingChatMessageContent"]]:
        raise NotImplementedError("Streaming is not supported for Copilot Studio agents.")

    # endregion

    # region Helper Methods

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

        prompt_parts: list[str] = []

        formatted_instructions = await self.format_instructions(kernel, arguments)
        if formatted_instructions:
            prompt_parts.append(formatted_instructions)

        if messages:
            prompt_parts.extend(messages)

        final_prompt: str = "\n".join(prompt_parts).strip()

        await self._ensure_conversation(thread)

        async for activity in self.client.ask_question(question=final_prompt, conversation_id=thread.id):
            if activity.type == ActivityTypes.message:
                if (
                    activity.text_format == "markdown"
                    and activity.suggested_actions
                    and activity.suggested_actions.actions
                ):
                    for action in activity.suggested_actions.actions:
                        if on_intermediate_message:
                            await on_intermediate_message(
                                ChatMessageContent(role=AuthorRole.ASSISTANT, name=self.name, content=action.text)
                            )
                yield ChatMessageContent(role=AuthorRole.ASSISTANT, name=self.name, content=activity.text)

    async def _ensure_conversation(self, thread: CopilotStudioAgentThread) -> None:
        """Guarantee that `thread.conversation_id` is populated."""
        if thread.id:
            return

        async for act in self.client.start_conversation():
            conversation_id = getattr(getattr(act, "conversation", None), "id", None)
            if conversation_id:
                thread.conversation_id = conversation_id
                return

        # If we reach this point, the service misbehaved, so throw
        raise AgentThreadOperationException("Copilot Studio did not return a conversation ID.")

    @staticmethod
    def _normalize_messages(messages: str | ChatMessageContent | list[str | ChatMessageContent] | None) -> list[str]:
        """Return a flat list[str] irrespective of the caller-supplied type."""
        if messages is None:
            return []

        if isinstance(messages, (str, ChatMessageContent)):
            messages = [messages]

        normalized: list[str] = []
        for m in messages:
            normalized.append(m.content if isinstance(m, ChatMessageContent) else str(m))
        return normalized

    @override
    async def _notify_thread_of_new_message(self, thread, new_message):
        """Copilot Studio Agent doesn't need to notify the thread of new messages.

        The new message is passed to the agent when invoking the agent.
        """
        pass

    # endregion
