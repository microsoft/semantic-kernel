# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class ModelDiagnosticSettings(KernelBaseSettings):
    """Settings for model diagnostics.

    The settings are first loaded from environment variables with
    the prefix 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_' are:
    - enable_otel_diagnostics: bool - Enable OpenTelemetry diagnostics. Default is False.
                (Env var SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS)
    - enable_otel_diagnostics_sensitive: bool - Enable OpenTelemetry sensitive events. Default is False.
                (Env var SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE)
    """

    env_prefix: ClassVar[str] = "SEMANTICKERNEL_EXPERIMENTAL_GENAI_"

    enable_otel_diagnostics: bool = False
    enable_otel_diagnostics_sensitive: bool = False
