# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, List, Optional

import openai
from numpy import array, ndarray

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class OpenAITextEmbedding(EmbeddingGeneratorBase):
    _model_id: str
    _api_key: str
    _api_type: Optional[str] = None
    _api_version: Optional[str] = None
    _endpoint: Optional[str] = None
    _org_id: Optional[str] = None
    _log: Logger

    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        api_type: Optional[str] = None,
        api_version: Optional[str] = None,
        endpoint: Optional[str] = None,
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
        self._api_type = api_type
        self._api_version = api_version
        self._endpoint = endpoint
        self._org_id = org_id
        self._log = log if log is not None else NullLogger()

    async def generate_embeddings_async(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        model_args = {}
        if self._api_type in ["azure", "azure_ad"]:
            model_args["engine"] = self._model_id
        else:
            model_args["model"] = self._model_id

        try:
            raw_embeddings = []
            batch_size = batch_size or len(texts)
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response: Any = await openai.Embedding.acreate(
                    **model_args,
                    api_key=self._api_key,
                    api_type=self._api_type,
                    api_base=self._endpoint,
                    api_version=self._api_version,
                    organization=self._org_id,
                    input=batch,
                )
                # make numpy arrays from the response
                raw_embeddings.extend([array(x["embedding"]) for x in response["data"]])
            return array(raw_embeddings)
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to generate embeddings",
                ex,
            )
