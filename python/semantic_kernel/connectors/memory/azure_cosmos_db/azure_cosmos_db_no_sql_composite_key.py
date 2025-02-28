# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureCosmosDBNoSQLCompositeKey(KernelBaseModel):
    """Azure CosmosDB NoSQL composite key."""

    partition_key: str
    key: str
