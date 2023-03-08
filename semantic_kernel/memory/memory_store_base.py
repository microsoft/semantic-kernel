# Copyright (c) Microsoft. All rights reserved.

from abc import ABC

from semantic_kernel.memory.storage.data_store_base import DataStoreBase
from semantic_kernel.ai.embeddings.embedding_index_base import EmbeddingIndexBase


class MemoryStoreBase(DataStoreBase, EmbeddingIndexBase, ABC):
    pass
