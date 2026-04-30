# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture


@fixture()
def perplexity_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for PerplexitySettings."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "PERPLEXITY_API_KEY": "test_api_key",
        "PERPLEXITY_CHAT_MODEL_ID": "sonar-pro",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars
