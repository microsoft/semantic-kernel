# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel
from semantic_kernel.utils.telemetry.model_diagnostics.model_diagnostics_settings import ModelDiagnosticSettings


@pytest.fixture()
def model_diagnostics_unit_test_env(monkeypatch):
    """Fixture to set environment variables for Model Diagnostics Unit Tests."""
    env_vars = {
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "true",
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "true",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Need to reload the settings to pick up the new environment variables since the
    # settings are loaded at import time and this fixture is called after the import
    semantic_kernel.utils.telemetry.agent_diagnostics.decorators.MODEL_DIAGNOSTICS_SETTINGS = ModelDiagnosticSettings()
