# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings
from semantic_kernel.kernel_pydantic import HttpsUrl
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureAISearchSettings(BaseModelSettings):
    """Azure AI Search model settings currently used by the AzureCognitiveSearchMemoryStore connector

    Optional:
    - api_key: SecretStr - Azure AI Search API key (Env var AZURE_AI_SEARCH_API_KEY)
    - endpoint: HttpsUrl - Azure AI Search endpoint (Env var AZURE_AI_SEARCH_ENDPOINT)
    - index_name: str - Azure AI Search index name (Env var AZURE_AI_SEARCH_INDEX_NAME)
    """

    api_key: SecretStr | None = None
    endpoint: HttpsUrl | None = None
    index_name: str | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "AZURE_AI_SEARCH_"

    def model_dump(self):
        """
        Custom method to dump model data in the required format.
        """
        return {
            "api_key": self.api_key.get_secret_value() if self.api_key else None,
            "endpoint": str(self.endpoint),
            "index_name": self.index_name,
        }
