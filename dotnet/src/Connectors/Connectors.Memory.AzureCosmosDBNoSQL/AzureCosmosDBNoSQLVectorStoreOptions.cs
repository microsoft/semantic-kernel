// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Options when creating a <see cref="AzureCosmosDBNoSQLVectorStore"/>.
/// </summary>
public sealed class AzureCosmosDBNoSQLVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TKey, TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public IAzureCosmosDBNoSQLVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Azure CosmosDB NoSQL record.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; init; }

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
