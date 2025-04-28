// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Options when creating a <see cref="AzureCosmosDBMongoDBVectorStore"/>
/// </summary>
public sealed class AzureCosmosDBMongoDBVectorStoreOptions
{
    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }

    /// <summary>
    /// An optional factory to use for constructing <see cref="AzureCosmosDBMongoDBVectorStoreRecordCollection{TKey, TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public IAzureCosmosDBMongoDBVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
