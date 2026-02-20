# Copyright (c) Microsoft. All rights reserved.

import pytest


@pytest.fixture()
def camb_unit_test_env(monkeypatch, exclude_list):
    """Fixture to set environment variables for CambSettings."""
    if exclude_list is None:
        exclude_list = []

    env_vars = {
        "CAMB_API_KEY": "test_api_key",
        "CAMB_TEXT_TO_AUDIO_MODEL_ID": "mars-flash",
    }

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars
