

      
# install the inference_client using pip:
# pip install -U inference_client
# from inference_client import Client
# import semantic_kernel as sk
# api_key, org_id = sk.jinaai_settings_from_dot_env()
# client = Client(token=api_key)
# model = client.get_model('ViT-B-32::laion2b-s34b-b79k')

# # Perform encode task
# embeddings = model.encode(
#     text=['First do it',
#     'then do it right',
#     'then do it better',]
# )
# print(embeddings)

# # Perform rank task
# candidates = [
#     'an image about dogs',
#     'an image about cats',
#     'an image about birds',
# ]
# image = 'https://picsum.photos/200'
# result = model.rank(image=image, candidates=candidates)
# print(result)

# Copyright (c) Microsoft. All rights reserved.

# from logging import Logger
# from typing import List, Optional

# from numpy import array, ndarray

# from semantic_kernel.connectors.ai.ai_exception import AIException
# from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
#     EmbeddingGeneratorBase,
# )
# from semantic_kernel.utils.null_logger import NullLogger


# class HuggingFaceTextEmbedding(EmbeddingGeneratorBase):
#     _model_id: str
#     _device: int
#     _log: Logger

#     def __init__(
#         self,
#         model_id: str,
#         device: Optional[int] = -1,
#         log: Optional[Logger] = None,
#     ) -> None:
#         """
#         Initializes a new instance of the HuggingFaceTextEmbedding class.

#         Arguments:
#             model_id {str} -- Hugging Face model card string, see
#                 https://huggingface.co/sentence-transformers
#             device {Optional[int]} -- Device to run the model on, -1 for CPU, 0+ for GPU.
#             log {Optional[Logger]} -- Logger instance.

#         Note that this model will be downloaded from the Hugging Face model hub.
#         """
#         self._model_id = model_id
#         self._log = log if log is not None else NullLogger()

#         try:
#             import sentence_transformers
#             import torch
#         except ImportError:
#             raise ImportError(
#                 "Please ensure that torch and sentence-transformers are installed to use HuggingFaceTextEmbedding"
#             )

#         self.device = (
#             "cuda:" + device if device >= 0 and torch.cuda.is_available() else "cpu"
#         )
#         self.generator = sentence_transformers.SentenceTransformer(
#             model_name_or_path=self._model_id, device=self.device
#         )

#     async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
#         """
#         Generates embeddings for a list of texts.

#         Arguments:
#             texts {List[str]} -- Texts to generate embeddings for.

#         Returns:
#             ndarray -- Embeddings for the texts.
#         """
#         try:
#             self._log.info(f"Generating embeddings for {len(texts)} texts")
#             embeddings = self.generator.encode(texts)
#             return array(embeddings)
#         except Exception as e:
#             raise AIException("Hugging Face embeddings failed", e)



# from inference_client import Client
# import semantic_kernel as sk
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
        try:
            # install the inference_client using pip:
            # pip install inference_client
            # import inference_client
            from inference_client import Client
            
        except ImportError:
            raise ImportError(
                "Please ensure that inference-client is installed to use JinaTextEmbedding"
            )

        # api_key, org_id = sk.jinaai_settings_from_dot_env()
        try:
            print("*********\n",api_key)
            self.client = Client(token=self._api_key)
        except Exception as f:
            raise AIException("Failed to get client started",f)
        self.model = self.client.get_model('ViT-B-32::laion2b-s34b-b79k')
        # try:
        #     self.generator = client.get_model('ViT-B-32::laion2b-s34b-b79k',)
        # except Exception as f:
        #     raise AIException("Failed to get Jina Model started",f)
        # self.device = (
        #     "cuda:" + device if device >= 0 and torch.cuda.is_available() else "cpu"
        # )
        # self.generator = sentence_transformers.SentenceTransformer(
        #     model_name_or_path=self._model_id, device=self.device
        # )


    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        try:
            self._log.info(f"Generating embeddings for {len(texts)} texts")
            
            embeddings = self.model.encode(text=texts)
            return array(embeddings)
        except Exception as e:
            raise AIException("Jina AI embeddings failed", e)



    # async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
    #     """
    #     Generates embeddings for a list of texts.

    #     Arguments:
    #         texts {List[str]} -- Texts to generate embeddings for.

    #     Returns:
    #         ndarray -- Embeddings for the texts.
    #     """
    #     print(texts)
    #     print(type(texts))
    #     try:
    #         self._log.info(f"Generating embeddings for {len(texts)} texts")
            
    #         embeddings = self.generator.encode(texts)
    #         return array(embeddings)
    #     except Exception as e:
    #         raise AIException("Jina AI embeddings failed", e)

    