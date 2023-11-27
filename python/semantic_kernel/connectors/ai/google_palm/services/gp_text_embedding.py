# Copyright (c) Microsoft. All rights reserved.


from typing import List

import google.generativeai as palm
from numpy import array, ndarray
from pydantic import constr

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)


class GooglePalmTextEmbedding(EmbeddingGeneratorBase, AIServiceClientBase):
    api_key: constr(strip_whitespace=True, min_length=1)

    def __init__(self, model_id: str, api_key: str) -> None:
        """
        Initializes a new instance of the GooglePalmTextEmbedding class.

        Arguments:
            model_id {str} -- GooglePalm model name, see
            https://developers.generativeai.google/models/language
            api_key {str} -- GooglePalm API key, see
            https://developers.generativeai.google/products/palm
        """
        super().__init__(model_id=model_id, api_key=api_key)

    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        """
        Generates embeddings for a list of texts.

        Arguments:
            texts {List[str]} -- Texts to generate embeddings for.

        Returns:
            ndarray -- Embeddings for the texts.
        """
        try:
            palm.configure(api_key=self.api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        embeddings = []
        for text in texts:
            try:
                response = palm.generate_embeddings(
                    model=self.model_id,
                    text=text,
                )
                embeddings.append(array(response["embedding"]))
            except Exception as ex:
                raise AIException(
                    AIException.ErrorCodes.ServiceError,
                    "Google PaLM service failed to generate the embedding.",
                    ex,
                )
        return array(embeddings)
