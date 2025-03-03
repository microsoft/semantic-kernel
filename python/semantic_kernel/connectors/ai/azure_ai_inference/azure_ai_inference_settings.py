# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureAIInferenceSettings(KernelBaseSettings):
    """Azure AI Inference settings.

    The settings are first loaded from environment variables with
    the prefix 'AZURE_AI_INFERENCE_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'AZURE_AI_INFERENCE_' are:
    - endpoint: HttpsUrl - The endpoint of the Azure AI Inference service deployment.
                This value can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal.
                (Env var AZURE_AI_INFERENCE_ENDPOINT)
    - api_key: SecretStr - The API key for the Azure AI Inference service deployment.
                This value can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal. You can use either KEY1 or KEY2.
                (Env var AZURE_AI_INFERENCE_API_KEY)
    """

    env_prefix: ClassVar[str] = "AZURE_AI_INFERENCE_"

    endpoint: HttpsUrl
    api_key: SecretStr | None = None
