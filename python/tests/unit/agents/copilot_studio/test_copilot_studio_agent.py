# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import TypeVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from microsoft.agents.copilotstudio.client import (
    CopilotClient,
)
from pydantic import SecretStr, ValidationError

import semantic_kernel.agents.copilot_studio.copilot_studio_agent as csa_mod
from semantic_kernel.agents import (
    CopilotStudioAgent,
    CopilotStudioAgentSettings,
    CopilotStudioAgentThread,
)
from semantic_kernel.agents.copilot_studio.copilot_studio_agent import (
    _CopilotStudioAgentTokenFactory,
)
from semantic_kernel.agents.copilot_studio.copilot_studio_agent_settings import CopilotStudioAgentAuthMode
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.exceptions import AgentInitializationException, AgentThreadInitializationException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template import PromptTemplateConfig

T = TypeVar("T")


@pytest.fixture
def aiter():
    async def _aiter(items: list[T]) -> AsyncIterator[T]:
        for item in items:
            yield item

    return _aiter


@pytest.fixture
def DummyConversation():
    class DummyConversation:
        def __init__(self, cid: str):
            self.id = cid

    return DummyConversation


@pytest.fixture
def DummyActivity(DummyConversation):
    class DummyActivity:
        def __init__(self, text: str, cid: str = "conv-123"):
            self.type = "message"
            self.text_format = "plain"
            self.text = text
            self.suggested_actions = None
            self.conversation = DummyConversation(cid)

    return DummyActivity


def test_initialize_thread_with_no_client_throws():
    with pytest.raises(AgentThreadInitializationException, match="CopilotClient cannot be None"):
        CopilotStudioAgentThread(client=None)


def test_normalize_messages():
    """All admissible inputs collapse to flat list[str]."""
    client = MagicMock(spec=CopilotClient)
    agent = CopilotStudioAgent(client=client)

    single_str = "hello"
    single_chat = ChatMessageContent(role=AuthorRole.USER, content="hola")
    mixed = [single_str, single_chat]

    assert agent._normalize_messages(None) == []
    assert agent._normalize_messages(single_str) == ["hello"]
    assert agent._normalize_messages(single_chat) == ["hola"]
    assert agent._normalize_messages(mixed) == ["hello", "hola"]


def test_plugin_warning_emitted_once(caplog):
    """If kernel already holds plugins the post-init hook issues one warning."""
    caplog.set_level(logging.WARNING)

    dummy_kernel = Kernel()
    dummy_kernel.add_plugin(SimpleNamespace(name="MyPlugin"))

    agent = CopilotStudioAgent(client=MagicMock(spec=CopilotClient), kernel=dummy_kernel)

    warn = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
    assert len(warn) == 1
    assert "plugins will be ignored" in warn[0].getMessage()

    # Clone the agent: no new warning expected
    caplog.clear()
    _ = agent.model_copy()
    assert not caplog.records


async def test_inner_invoke_prompt_and_yield(monkeypatch, aiter, DummyActivity):
    client = MagicMock(spec=CopilotClient)
    prompts: dict[str, str] = {}

    async def fake_ask_question(*, question: str, conversation_id: str):
        prompts["sent"] = question
        yield DummyActivity("Aye matey!")

    client.ask_question.side_effect = fake_ask_question
    client.start_conversation = lambda: aiter([DummyActivity("", "conv-123")])

    monkeypatch.setattr(
        CopilotStudioAgent,
        "format_instructions",
        AsyncMock(return_value="Respond like a pirate"),
    )

    agent = CopilotStudioAgent(client=client)
    thread = CopilotStudioAgentThread(client=client)

    replies = [
        msg
        async for msg in agent._inner_invoke(
            thread=thread, messages=["Tell me a joke about bears", "make the joke kid friendly"]
        )
    ]

    expected_prompt = "Respond like a pirate\nTell me a joke about bears\nmake the joke kid friendly"
    assert prompts["sent"] == expected_prompt
    assert len(replies) == 1
    assert replies[0].content == "Aye matey!"
    assert replies[0].role is AuthorRole.ASSISTANT


async def test_get_response(monkeypatch, aiter, DummyActivity):
    client = MagicMock(spec=CopilotClient)
    sent: dict[str, str] = {}

    async def fake_ask_question(*, question: str, conversation_id: str):
        sent["cid"] = conversation_id
        yield DummyActivity("first", conversation_id)
        yield DummyActivity("second", conversation_id)

    client.ask_question.side_effect = fake_ask_question
    client.start_conversation = lambda: aiter([DummyActivity("", "conv-123")])

    monkeypatch.setattr(
        CopilotStudioAgent,
        "format_instructions",
        AsyncMock(return_value=None),
    )

    agent = CopilotStudioAgent(client=client)
    thread = CopilotStudioAgentThread(client=client)

    item = await agent.get_response(messages="hi there", thread=thread)

    assert item.message.content == "second"
    assert thread.id == "conv-123"
    assert sent["cid"] == "conv-123"
    assert item.thread is thread


async def test_invoke(monkeypatch, aiter, DummyActivity):
    client = MagicMock(spec=CopilotClient)
    sent: dict[str, str] = {}

    async def fake_ask_question(*, question: str, conversation_id: str):
        sent["cid"] = conversation_id
        yield DummyActivity("first", conversation_id)
        yield DummyActivity("second", conversation_id)

    client.ask_question.side_effect = fake_ask_question

    client.start_conversation = lambda: aiter([DummyActivity("", "conv-123")])

    monkeypatch.setattr(
        CopilotStudioAgent,
        "format_instructions",
        AsyncMock(return_value=None),
    )

    agent = CopilotStudioAgent(
        client=client, prompt_template_config=PromptTemplateConfig(template="Handle the message in this {{$style}}")
    )
    thread = CopilotStudioAgentThread(client=client)

    responses = []
    async for response in agent.invoke(messages="hi there", thread=thread, arguments=KernelArguments(style="funny")):
        responses.append(response)

    item = responses[-1]
    assert item.message.content == "second"
    assert thread.id == "conv-123"
    assert sent["cid"] == "conv-123"
    assert item.thread is thread


def test_setup_resources_settings_validation_error():
    sentinel_exc = ValidationError.from_exception_data("dummy", [], input_type="python")

    with (
        patch(
            "semantic_kernel.agents.copilot_studio.copilot_studio_agent.CopilotStudioAgentSettings",
            side_effect=sentinel_exc,
        ),
        pytest.raises(
            AgentInitializationException,
            match="Failed to create Copilot Studio Agent settings",
        ),
    ):
        _ = CopilotStudioAgent.create_client(app_client_id="appid", tenant_id="tenantid")


def test_setup_resources_missing_ids():
    dummy_settings = MagicMock(spec=CopilotStudioAgentSettings)
    dummy_settings.app_client_id = None
    dummy_settings.tenant_id = None

    with (
        patch(
            "semantic_kernel.agents.copilot_studio.copilot_studio_agent.CopilotStudioAgentSettings",
            return_value=dummy_settings,
        ),
        pytest.raises(
            AgentInitializationException,
            match="Missing required configuration field\\(s\\): app_client_id, tenant_id",
        ),
    ):
        _ = CopilotStudioAgent.create_client()


def test_setup_resources_happy_path(tmp_path, monkeypatch):
    dummy_settings = MagicMock(spec=CopilotStudioAgentSettings)
    dummy_settings.app_client_id = "appid"
    dummy_settings.tenant_id = "tenantid"
    dummy_settings.auth_mode = CopilotStudioAgentAuthMode.INTERACTIVE
    dummy_settings.client_secret = SecretStr("test-secret")

    monkeypatch.setattr(
        "semantic_kernel.agents.copilot_studio.copilot_studio_agent.CopilotStudioAgentSettings",
        lambda **_: dummy_settings,
    )

    monkeypatch.setattr(
        _CopilotStudioAgentTokenFactory,
        "acquire",
        lambda self: "fake-token",
    )

    sentinel_client = MagicMock(spec=CopilotClient)
    with patch(
        "semantic_kernel.agents.copilot_studio.copilot_studio_agent.CopilotClient",
        return_value=sentinel_client,
    ) as mock_client_ctor:
        cache_path = tmp_path / "cache.bin"
        monkeypatch.setenv("TOKEN_CACHE_PATH", str(cache_path))

        returned = CopilotStudioAgent.create_client(
            app_client_id="appid",
            tenant_id="tenantid",
            environment_id="env-id",
            agent_identifier="agent-name",
            auth_mode=CopilotStudioAgentAuthMode.SERVICE,
        )

    mock_client_ctor.assert_called_once_with(dummy_settings, "fake-token")
    assert returned is sentinel_client


class DummyCache:
    """Mock cache for PersistedTokenCache; avoids disk I/O."""

    pass


class FakeAppSilent:
    def __init__(self, client_id, authority, token_cache, client_credential=None, **kwargs):
        pass

    def get_accounts(self):
        return [{"home_account_id": "acct1"}]

    def acquire_token_silent(self, scopes, account):
        return {"access_token": "silent-token"}

    def acquire_token_interactive(self, scopes):
        pytest.skip("Unexpected interactive flow in silent test")


class FakeAppInteractive:
    def __init__(self, client_id, authority, token_cache):
        pass

    def get_accounts(self):
        return []

    def acquire_token_silent(self, scopes, account):
        pytest.skip("Unexpected silent flow in interactive test")

    def acquire_token_interactive(self, scopes):
        return {"access_token": "interactive-token"}


class FakeAppError:
    def __init__(self, client_id, authority, token_cache):
        pass

    def get_accounts(self):
        return []

    def acquire_token_silent(self, scopes, account):
        return {}

    def acquire_token_interactive(self, scopes):
        return {
            "error": "bad",
            "error_description": "failed",
            "correlation_id": "cid",
        }


@pytest.fixture(autouse=True)
def stub_cache(monkeypatch):
    monkeypatch.setattr(
        _CopilotStudioAgentTokenFactory,
        "_get_msal_token_cache",
        staticmethod(lambda cache_path, fallback_to_plaintext=True: DummyCache()),
    )


@pytest.mark.parametrize(
    "fake_app, expected_token, mode",
    [
        pytest.param(
            FakeAppSilent,
            "silent-token",
            CopilotStudioAgentAuthMode.SERVICE,
            marks=pytest.mark.skip(reason="Skipping SERVICE auth mode test as the mode is not yet supported."),
        ),
        (FakeAppInteractive, "interactive-token", CopilotStudioAgentAuthMode.INTERACTIVE),
    ],
)
def test_acquire_token_success(monkeypatch, tmp_path, fake_app, expected_token, mode):
    settings = CopilotStudioAgentSettings(app_client_id="id", tenant_id="tid")
    cache_path = str(tmp_path / "cache.bin")

    monkeypatch.setattr(csa_mod, "PublicClientApplication", fake_app)
    monkeypatch.setattr(csa_mod, "ConfidentialClientApplication", fake_app)

    client_secret = None
    if fake_app == FakeAppSilent:
        client_secret = "test-secret"

    factory = _CopilotStudioAgentTokenFactory(
        settings=settings,
        cache_path=cache_path,
        mode=mode,
        client_secret=client_secret,
        client_certificate=None,
        user_assertion=None,
    )
    token = factory.acquire()
    assert token == expected_token


def test_acquire_token_error(monkeypatch, tmp_path):
    settings = CopilotStudioAgentSettings(app_client_id="id", tenant_id="tid")
    cache_path = str(tmp_path / "cache.bin")

    monkeypatch.setattr(csa_mod, "PublicClientApplication", FakeAppError)
    monkeypatch.setattr(csa_mod, "ConfidentialClientApplication", FakeAppError)

    factory = _CopilotStudioAgentTokenFactory(
        settings=settings,
        cache_path=cache_path,
        mode=CopilotStudioAgentAuthMode.INTERACTIVE,
        client_secret=None,
        client_certificate=None,
        user_assertion=None,
    )
    with pytest.raises(AgentInitializationException):
        factory.acquire()
