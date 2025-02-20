// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Options when creating a <see cref="AzureCosmosDBMongoDBVectorStore"/>
/// </summary>
public sealed class AzureCosmosDBMongoDBVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="AzureCosmosDBMongoDBVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public IAzureCosmosDBMongoDBVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
