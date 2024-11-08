# Copyright (c) Microsoft. All rights reserved.

from azure.cosmos.partition_key import PartitionKey

from semantic_kernel.connectors.memory.azure_cosmos_db.const import COSMOS_ITEM_ID_PROPERTY_NAME
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureCosmosDBNoSQLCompositeKey(KernelBaseModel):
    """Azure CosmosDB NoSQL composite key."""

    partition_key: str
    key: str

    @classmethod
    def from_record(cls, record: dict[str, str], partition_key: PartitionKey) -> "AzureCosmosDBNoSQLCompositeKey":
        """Create an AzureCosmosDBNoSQLCompositeKey from a record.

        Args:
            record (dict): The record.
            partition_key (PartitionKey): The partition key.

        Returns:
            AzureCosmosDBNoSQLCompositeKey: The AzureCosmosDBNoSQLCompositeKey.
        """
        return cls(partition_key=record[partition_key.path.strip("/")], key=record[COSMOS_ITEM_ID_PROPERTY_NAME])
