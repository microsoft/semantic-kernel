// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// Options when creating a <see cref="CosmosNoSqlVectorStore"/>.
/// </summary>
public sealed class CosmosNoSqlVectorStoreOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlVectorStoreOptions"/> class.
    /// </summary>
    public CosmosNoSqlVectorStoreOptions()
    {
    }

    internal CosmosNoSqlVectorStoreOptions(CosmosNoSqlVectorStoreOptions? source)
    {
        this.JsonSerializerOptions = source?.JsonSerializerOptions;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Azure CosmosDB NoSQL record.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; set; }

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
