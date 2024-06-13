# Copyright (c) Microsoft. All rights reserved.


from typing import Generic, TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

DataModelT = TypeVar("DataModelT")


class MemoryPlugin(KernelBaseModel, Generic[DataModelT]):
    memory_store: MemoryStoreBase
    collection_name: str
