# Copyright (c) Microsoft. All rights reserved.

import importlib

from semantic_kernel.const import USER_AGENT
from semantic_kernel.utils.telemetry.user_agent import (
    HTTP_USER_AGENT,
    TELEMETRY_DISABLED_ENV_VAR,
    prepend_semantic_kernel_to_user_agent,
)


def test_append_to_existing_user_agent(monkeypatch):
    monkeypatch.setenv(TELEMETRY_DISABLED_ENV_VAR, "false")
    monkeypatch.setattr("importlib.metadata.version", lambda _: "1.0.0")
    monkeypatch.setattr("semantic_kernel.utils.telemetry.user_agent.version_info", "1.0.0")

    # need to reload the module to get the updated version number
    import semantic_kernel.utils.telemetry.user_agent

    importlib.reload(semantic_kernel.utils.telemetry.user_agent)

    headers = {USER_AGENT: "existing-agent"}
    expected = {USER_AGENT: f"{HTTP_USER_AGENT}/1.0.0 existing-agent"}
    result = prepend_semantic_kernel_to_user_agent(headers)
    assert result == expected


def test_create_new_user_agent(monkeypatch):
    monkeypatch.setenv(TELEMETRY_DISABLED_ENV_VAR, "false")
    monkeypatch.setattr("importlib.metadata.version", lambda _: "1.0.0")
    monkeypatch.setattr("semantic_kernel.utils.telemetry.user_agent.version_info", "1.0.0")

    # need to reload the module to get the updated version number
    import semantic_kernel.utils.telemetry.user_agent

    importlib.reload(semantic_kernel.utils.telemetry.user_agent)

    headers = {}
    expected = {USER_AGENT: f"{HTTP_USER_AGENT}/1.0.0"}
    result = prepend_semantic_kernel_to_user_agent(headers)
    assert result == expected


def test_telemetry_disabled(monkeypatch):
    monkeypatch.setenv(TELEMETRY_DISABLED_ENV_VAR, "true")
    monkeypatch.setattr("importlib.metadata.version", lambda _: "1.0.0")
    monkeypatch.setattr("semantic_kernel.utils.telemetry.user_agent.version_info", "1.0.0")

    headers = {}
    result = prepend_semantic_kernel_to_user_agent(headers)
    assert result == headers


def test_app_info_when_telemetry_enabled(monkeypatch):
    monkeypatch.setenv(TELEMETRY_DISABLED_ENV_VAR, "false")
    monkeypatch.setattr("importlib.metadata.version", lambda _: "1.0.0")
    monkeypatch.setattr("semantic_kernel.utils.telemetry.user_agent.version_info", "1.0.0")

    # need to reload the module to get the updated APP_INFO
    import semantic_kernel.utils.telemetry.user_agent

    importlib.reload(semantic_kernel.utils.telemetry.user_agent)

    expected = {"semantic-kernel-version": "python/1.0.0"}
    assert expected == semantic_kernel.utils.telemetry.user_agent.APP_INFO


def test_app_info_when_telemetry_disabled(monkeypatch):
    monkeypatch.setenv(TELEMETRY_DISABLED_ENV_VAR, "true")
    monkeypatch.setattr("importlib.metadata.version", lambda _: "1.0.0")
    monkeypatch.setattr("semantic_kernel.utils.telemetry.user_agent.version_info", "1.0.0")

    # need to reload the module to get the updated APP_INFO
    import semantic_kernel.utils.telemetry.user_agent

    importlib.reload(semantic_kernel.utils.telemetry.user_agent)

    assert semantic_kernel.utils.telemetry.user_agent.APP_INFO is None
