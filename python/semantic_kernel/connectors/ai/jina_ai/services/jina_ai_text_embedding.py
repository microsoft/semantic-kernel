from logging import Logger
from typing import Any, List, Optional
import semantic_kernel as sk

from numpy import array, ndarray

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.utils.null_logger import NullLogger

class JinaTextEmbedding(EmbeddingGeneratorBase):
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
        Initializes a new instance of the JinaTextCompletion class.

        Arguments:
            model_id {str} -- JinaAI model name, see
                https://cloud.jina.ai/user/inference
            api_key {str} -- JinaAI API key, see
                https://cloud.jina.ai/settings/tokens
            org_id {Optional[str]} -- JinaAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
        """
        self._model_id = model_id
        self._api_key = api_key
        self._org_id = org_id
        self._log = log if log is not None else NullLogger()
        try:
            # install the inference_client using pip:
            # pip install inference_client
            # import inference_client
            from inference_client import Client
            
        except ImportError:
            raise ImportError(
                "Please ensure that inference-client is installed to use JinaTextEmbedding"
            )

        try:
            self.client = Client(token=self._api_key)
        except Exception as f:
            raise AIException("Failed to get client started",f)
        self.model = self.client.get_model(self._model_id)


    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        try:
            self._log.info(f"Generating embeddings for {len(texts)} texts")
            
            embeddings = self.model.encode(text=texts)
            return array(embeddings)
        except Exception as e:
            raise AIException("Jina AI embeddings failed", e)

    