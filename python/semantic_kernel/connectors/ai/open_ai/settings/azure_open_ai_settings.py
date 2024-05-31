# Copyright (c) Microsoft. All rights reserved.


from pydantic import SecretStr
from pydantic_settings import BaseSettings

from semantic_kernel.kernel_pydantic import HttpsUrl


class AzureOpenAISettings(BaseSettings):
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
                under Management > Deployments in Azure OpenAI Studio.
                (Env var AZURE_OPENAI_CHAT_DEPLOYMENT_NAME)
    - text_deployment_name: str - The name of the Azure Text deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
                (Env var AZURE_OPENAI_TEXT_DEPLOYMENT_NAME)
    - embedding_deployment_name: str - The name of the Azure Embedding deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
                (Env var AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME)
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
    - env_file_path: str | None - if provided, the .env settings are read from this file path location
    """

    env_file_path: str | None = None
    chat_deployment_name: str | None = None
    text_deployment_name: str | None = None
    embedding_deployment_name: str | None = None
    endpoint: HttpsUrl | None = None
    base_url: HttpsUrl | None = None
    api_key: SecretStr | None = None
    api_version: str | None = None

    class Config:
        """Pydantic configuration settings."""

        env_prefix = "AZURE_OPENAI_"
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        """Create an instance of the class."""
        if "env_file_path" in kwargs and kwargs["env_file_path"]:
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
