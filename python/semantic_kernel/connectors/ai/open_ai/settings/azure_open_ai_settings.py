# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr
from pydantic_core import Url

from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings
from semantic_kernel.utils.authentication.entra_id_authentication import get_entra_auth_token


class AzureOpenAISettings(KernelBaseSettings):
    """AzureOpenAI model settings.

    The settings are first loaded from environment variables with the prefix 'AZURE_OPENAI_'.
    If the environment variables are not found, the settings can be loaded from a .env file
    with the encoding 'utf-8'. If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'AZURE_OPENAI_' are:
    - chat_deployment_name: str - The name of the Azure Chat deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_CHAT_DEPLOYMENT_NAME)
    - responses_deployment_name: str - The name of the Azure Responses deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME)
    - text_deployment_name: str - The name of the Azure Text deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_TEXT_DEPLOYMENT_NAME)
    - embedding_deployment_name: str - The name of the Azure Embedding deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME)
    - text_to_image_deployment_name: str - The name of the Azure Text to Image deployment. This
                value will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME)
    - audio_to_text_deployment_name: str - The name of the Azure Audio to Text deployment. This
                value will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME)
    - text_to_audio_deployment_name: str - The name of the Azure Text to Audio deployment. This
                value will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME)
    - realtime_deployment_name: str - The name of the Azure Realtime deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure AI Foundry.
                (Env var AZURE_OPENAI_REALTIME_DEPLOYMENT_NAME)
    - api_key: SecretStr - The API key for the Azure deployment. This value can be
                found in the Keys & Endpoint section when examining your resource in
                the Azure portal. You can use either KEY1 or KEY2.
                (Env var AZURE_OPENAI_API_KEY)
    - base_url: HttpsUrl | None - base_url: The url of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the base_url consists of the endpoint,
                followed by /openai/deployments/{deployment_name}/,
                use endpoint if you only want to supply the endpoint.
                (Env var AZURE_OPENAI_BASE_URL)
    - endpoint: HttpsUrl - The endpoint of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the endpoint should end in openai.azure.com.
                If both base_url and endpoint are supplied, base_url will be used.
                (Env var AZURE_OPENAI_ENDPOINT)
    - api_version: str | None - The API version to use. The default value is "2024-02-01".
                (Env var AZURE_OPENAI_API_VERSION)
    - token_endpoint: str - The token endpoint to use to retrieve the authentication token.
                The default value is "https://cognitiveservices.azure.com/.default".
                (Env var AZURE_OPENAI_TOKEN_ENDPOINT)
    """

    env_prefix: ClassVar[str] = "AZURE_OPENAI_"

    chat_deployment_name: str | None = None
    responses_deployment_name: str | None = None
    text_deployment_name: str | None = None
    embedding_deployment_name: str | None = None
    text_to_image_deployment_name: str | None = None
    audio_to_text_deployment_name: str | None = None
    text_to_audio_deployment_name: str | None = None
    realtime_deployment_name: str | None = None
    endpoint: HttpsUrl | None = None
    base_url: Url | None = None
    api_key: SecretStr | None = None
    api_version: str = DEFAULT_AZURE_API_VERSION
    token_endpoint: str = "https://cognitiveservices.azure.com/.default"

    def get_azure_openai_auth_token(self, token_endpoint: str | None = None) -> str | None:
        """Retrieve a Microsoft Entra Auth Token for a given token endpoint for the use with Azure OpenAI.

        The required role for the token is `Cognitive Services OpenAI Contributor`.
        The token endpoint may be specified as an environment variable, via the .env
        file or as an argument. If the token endpoint is not provided, the default is None.
        The `token_endpoint` argument takes precedence over the `token_endpoint` attribute.

        Args:
            token_endpoint: The token endpoint to use. Defaults to `https://cognitiveservices.azure.com/.default`.

        Returns:
            The Azure token or None if the token could not be retrieved.

        Raises:
            ServiceInitializationError: If the token endpoint is not provided.
        """
        endpoint_to_use = token_endpoint or self.token_endpoint
        if endpoint_to_use is None:
            raise ServiceInitializationError("Please provide a token endpoint to retrieve the authentication token.")
        return get_entra_auth_token(endpoint_to_use)
