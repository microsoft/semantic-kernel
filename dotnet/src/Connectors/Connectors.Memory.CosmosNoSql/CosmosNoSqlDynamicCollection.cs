// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Microsoft.Azure.Cosmos;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// Represents a collection of vector store records in a CosmosNoSql database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class CosmosNoSqlDynamicCollection : CosmosNoSqlCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlDynamicCollection"/> class.
    /// </summary>
    /// <param name="database"><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public CosmosNoSqlDynamicCollection(Database database, string name, CosmosNoSqlCollectionOptions options)
        : this(
            new(database.Client, ownsClient: false),
            _ => database,
            name,
            options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="clientOptions">Optional configuration options for <see cref="CosmosClient"/>.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public CosmosNoSqlDynamicCollection(
        string connectionString,
        string databaseName,
        string collectionName,
        CosmosClientOptions? clientOptions = null,
        CosmosNoSqlCollectionOptions? options = null)
        : this(
            new(new CosmosClient(connectionString, clientOptions), ownsClient: true),
            client => client.GetDatabase(databaseName),
            collectionName,
            options)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);
        Verify.NotNullOrWhiteSpace(collectionName);
    }

    internal CosmosNoSqlDynamicCollection(
        ClientWrapper clientWrapper,
        Func<CosmosClient, Database> databaseProvider,
        string name,
        CosmosNoSqlCollectionOptions? options)
        : base(
            clientWrapper,
            databaseProvider,
            name,
            static options => new CosmosNoSqlModelBuilder()
                .BuildDynamic(
                    options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                    options.EmbeddingGenerator,
                    options.JsonSerializerOptions ?? JsonSerializerOptions.Default),
            options)
    {
    }
}
