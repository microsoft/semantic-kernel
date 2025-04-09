// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Composite key for Azure CosmosDB NoSQL record with record and partition keys.
/// </summary>
public sealed class AzureCosmosDBNoSQLCompositeKey(string recordKey, string partitionKey)
{
    /// <summary>
    /// Value of record key.
    /// </summary>
    public string RecordKey { get; } = recordKey;

    /// <summary>
    /// Value of partition key.
    /// </summary>
    public string PartitionKey { get; } = partitionKey;
}
