# Copyright (c) Microsoft. All rights reserved.


from pydantic import SecretStr
from pydantic_settings import BaseSettings

from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.kernel_pydantic import HttpsUrl


class AzureOpenAISettings(BaseSettings):
    """AzureOpenAI model settings

    The settings are first loaded from environment variables with the prefix 'AZURE_OPENAI_'.
    If the environment variables are not found, the settings can be loaded from a .env file
    with the encoding 'utf-8'. If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'AZURE_OPENAI_' are:
    - deployment_name: str - The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
    - api_key: SecretStr - The API key for the Azure deployment. This value can be
                found in the Keys & Endpoint section when examining your resource in
                the Azure portal. You can use either KEY1 or KEY2.

    Optional settings for prefix 'AZURE_OPENAI_' are:
    - base_url: HttpsUrl | None - base_url: The url of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the base_url consists of the endpoint,
                followed by /openai/deployments/{deployment_name}/,
                use endpoint if you only want to supply the endpoint.
    - endpoint: HttpsUrl - The endpoint of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the endpoint should end in openai.azure.com.
                If both base_url and endpoint are supplied, base_url will be used.
    - api_version: str | None - The API version to use. The default value is "2023-05-15".
    """

    use_env_settings_file: bool = False
    chat_deployment_name: str = "gpt-35-turbo"
    text_deployment_name: str = "gpt-35-turbo-instruct"
    embedding_deployment_name: str = "text-embedding-ada-002"  # TODO don't have this as default
    endpoint: HttpsUrl | None = None
    base_url: HttpsUrl | None = None
    api_key: SecretStr = None
    api_version: str = DEFAULT_AZURE_API_VERSION

    class Config:
        env_prefix = "AZURE_OPENAI_"
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        if kwargs.pop("use_env_settings_file", False):
            cls.Config.env_file = ".env"
        return cls(**kwargs)
