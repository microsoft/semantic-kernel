// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Options when creating a <see cref="AzureCosmosDBNoSQLVectorStore"/>.
/// </summary>
public sealed class AzureCosmosDBNoSQLVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
    /// </summary>
    public IAzureCosmosDBNoSQLVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
