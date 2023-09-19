# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import List, Optional

from numpy import ndarray

from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_service_calls import (
    OpenAIModelTypes,
)


class AzureTextEmbedding(AzureTextCompletion, EmbeddingGeneratorBase):
    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2022-12-01",
        log: Optional[Logger] = None,
        logger: Optional[Logger] = None,
        ad_auth=False,
    ) -> None:
        """
        Initialize an AzureTextEmbedding service.

        You must provide:
        - A deployment_name, endpoint, and api_key (plus, optionally: ad_auth)

        :param deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        :param endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal.
        :param api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        :param api_version: The API version to use. (Optional)
            The default value is "2022-12-01".
        :param logger: The logger instance to use. (Optional)
        :param ad_auth: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        """
        if logger:
            logger.warning("The 'logger' argument is deprecated, use 'log' instead.")
        super().__init__(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=log or logger,
            ad_auth=ad_auth,
        )
        self.model_type = OpenAIModelTypes.EMBEDDING

    async def generate_embeddings_async(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        return await self._send_embedding_request(texts, batch_size)

    async def complete_stream_async(
        self,
        prompt: str,
        settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        raise NotImplementedError(
            "Embedding class does not currently support completions"
        )

    async def complete_async(
        self,
        prompt: str,
        settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        raise NotImplementedError(
            "Embedding class does not currently support completions"
        )
