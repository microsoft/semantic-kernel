// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Options when creating a <see cref="CosmosNoSqlCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class CosmosNoSqlCollectionOptions
{
    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreKeyAttribute"/>, <see cref="VectorStoreDataAttribute"/> and <see cref="VectorStoreVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Azure CosmosDB NoSQL record.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; init; } = null;

    /// <summary>
    /// The property name to use as partition key.
    /// </summary>
    public string? PartitionKeyPropertyName { get; init; } = null;

    /// <summary>
    /// Specifies the indexing mode in the Azure Cosmos DB service.
    /// More information here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/index-policy#indexing-mode"/>.
    /// </summary>
    /// <remarks>
    /// Default is <see cref="IndexingMode.Consistent" />.
    /// </remarks>
    public IndexingMode IndexingMode { get; init; } = IndexingMode.Consistent;

    /// <summary>
    /// Gets or sets a value that indicates whether automatic indexing is enabled for a collection in the Azure Cosmos DB service.
    /// </summary>
    /// <remarks>
    /// Default is <see langword="true" />.
    /// </remarks>
    public bool Automatic { get; init; } = true;

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
