# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureCosmosDBNoSQLCompositeKey(KernelBaseModel):
    """Azure CosmosDB NoSQL composite key."""

    partition_key: str
    key: str
