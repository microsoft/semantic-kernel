# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, List, Optional

from numpy import array, ndarray

from semantic_kernel.ai.ai_exception import AIException
from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class OpenAITextEmbedding(EmbeddingGeneratorBase):
    _model_id: str
    _api_key: str
    _org_id: Optional[str] = None
    _log: Logger

    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initializes a new instance of the OpenAITextCompletion class.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
        """
        self._model_id = model_id
        self._api_key = api_key
        self._org_id = org_id
        self._log = log if log is not None else NullLogger()

    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        import openai

        openai.api_key = self._api_key
        if self._org_id is not None:
            openai.organization = self._org_id

        try:
            response: Any = await openai.Embedding.acreate(
                model=self._model_id,
                input=texts,
            )

            # make numpy arrays from the response
            raw_embeddings = [array(x["embedding"]) for x in response["data"]]
            return array(raw_embeddings)
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to generate embeddings",
                ex,
            )
