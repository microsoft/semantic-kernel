# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture


@fixture
def aca_python_sessions_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for ACA Python Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "ACA_POOL_MANAGEMENT_ENDPOINT": "https://test.endpoint/",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars
