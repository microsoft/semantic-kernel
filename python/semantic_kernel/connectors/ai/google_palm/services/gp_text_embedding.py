# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Any, List

import google.generativeai as palm
from numpy import array, ndarray
from pydantic import StringConstraints, ValidationError

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.settings.google_palm_settings import GooglePalmSettings
from semantic_kernel.exceptions import ServiceInvalidAuthError, ServiceResponseException
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class GooglePalmTextEmbedding(EmbeddingGeneratorBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

    def __init__(self, ai_model_id: str, use_env_settings_file: bool = False) -> None:
        """
        Initializes a new instance of the GooglePalmTextEmbedding class.

        Arguments:
            ai_model_id {str} -- GooglePalm model name, see
                https://developers.generativeai.google/models/language
            use_env_settings_file {bool} -- Use the environment settings file
                as a fallback to environment variables. (Optional)
        """
        try:
            google_palm_settings = GooglePalmSettings.create(use_env_settings_file=use_env_settings_file)
        except ValidationError as e:
            logger.error(f"Error loading Google Palm settings: {e}")
            raise ServiceInitializationError("Error loading Google Palm settings") from e
        api_key = google_palm_settings.api_key.get_secret_value()
        super().__init__(ai_model_id=ai_model_id, api_key=api_key)

    async def generate_embeddings(self, texts: List[str], **kwargs: Any) -> ndarray:
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
            raise ServiceInvalidAuthError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            ) from ex
        embeddings = []
        for text in texts:
            try:
                response = palm.generate_embeddings(model=self.ai_model_id, text=text, **kwargs)
                embeddings.append(array(response["embedding"]))
            except Exception as ex:
                raise ServiceResponseException(
                    "Google PaLM service failed to generate the embedding.",
                    ex,
                ) from ex
        return array(embeddings)
