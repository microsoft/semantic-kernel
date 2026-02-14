// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// Options when creating a <see cref="CosmosNoSqlCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class CosmosNoSqlCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly CosmosNoSqlCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlVectorStoreOptions"/> class.
    /// </summary>
    public CosmosNoSqlCollectionOptions()
    {
    }

    internal CosmosNoSqlCollectionOptions(CosmosNoSqlCollectionOptions? source) : base(source)
    {
        this.JsonSerializerOptions = source?.JsonSerializerOptions;
        this.PartitionKeyPropertyNames = source?.PartitionKeyPropertyNames is { Count: > 0 } names ? [.. names] : [];
        this.IndexingMode = source?.IndexingMode ?? Default.IndexingMode;
        this.Automatic = source?.Automatic ?? Default.Automatic;
    }

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Azure CosmosDB NoSQL record.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; set; }

    /// <summary>
    /// Gets or sets the property names to use as partition key components.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Cosmos DB supports up to 3 levels of hierarchical partition keys. Provide the property names in hierarchical order.
    /// For a single partition key, provide a list with one element. For hierarchical partition keys, provide up to 3 elements.
    /// </para>
    /// <para>
    /// Selecting a partition key is critical for performance and scalability. Choose properties with high cardinality
    /// that evenly distribute requests. See <see href="https://learn.microsoft.com/azure/cosmos-db/partitioning-overview"/> for guidance.
    /// </para>
    /// <para>
    /// If empty, you must use <see cref="CosmosNoSqlKey"/> as the key type with an explicitly constructed
    /// <see cref="PartitionKey"/>. If your scenario does not require partitioning, use <see cref="PartitionKey.None"/>,
    /// though this is not recommended for production workloads.
    /// </para>
    /// </remarks>
    public IReadOnlyList<string> PartitionKeyPropertyNames { get; set; } = [];

    /// <summary>
    /// Specifies the indexing mode in the Azure Cosmos DB service.
    /// More information here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/index-policy#indexing-mode"/>.
    /// </summary>
    /// <remarks>
    /// Default is <see cref="IndexingMode.Consistent" />.
    /// </remarks>
    public IndexingMode IndexingMode { get; set; } = IndexingMode.Consistent;

    /// <summary>
    /// Gets or sets a value that indicates whether automatic indexing is enabled for a collection in the Azure Cosmos DB service.
    /// </summary>
    /// <remarks>
    /// Default is <see langword="true" />.
    /// </remarks>
    public bool Automatic { get; set; } = true;
}
