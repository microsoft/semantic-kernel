﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a vector store implementation using PostgreSQL.
/// </summary>
public sealed class PostgresVectorStore : VectorStore
{
    private readonly IPostgresVectorStoreDbClient _postgresClient;
    private readonly NpgsqlDataSource? _dataSource;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>The database schema.</summary>
    private readonly string _schema;

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="options">Optional configuration options for this class</param>
    public PostgresVectorStore(NpgsqlDataSource dataSource, PostgresVectorStoreOptions? options = default)
    {
        this._dataSource = dataSource;

        options ??= new();
        this._schema = options.Schema;
        this._embeddingGenerator = options.EmbeddingGenerator;
        this._postgresClient = new PostgresDbClient(this._dataSource, this._schema);

        this._metadata = new()
        {
            VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
            VectorStoreName = this._postgresClient.DatabaseName
        };
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="postgresDbClient">An instance of <see cref="IPostgresVectorStoreDbClient"/>.</param>
    /// <param name="options">Optional configuration options for this class</param>
    internal PostgresVectorStore(IPostgresVectorStoreDbClient postgresDbClient, PostgresVectorStoreOptions? options = default)
    {
        this._postgresClient = postgresDbClient;

        options ??= PostgresVectorStoreOptions.Default;
        this._schema = options.Schema;
        this._embeddingGenerator = options.EmbeddingGenerator;

        this._metadata = new()
        {
            VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
            VectorStoreName = this._postgresClient.DatabaseName
        };
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return PostgresUtils.WrapAsyncEnumerableAsync(
            this._postgresClient.GetTablesAsync(cancellationToken),
            "ListCollectionNames",
            this._metadata
        );
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
#if NET8_0_OR_GREATER
    public override PostgresCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#endif
        => new PostgresCollection<TKey, TRecord>(
            this._postgresClient,
            name,
            new PostgresCollectionOptions()
            {
                Schema = this._schema,
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._embeddingGenerator,
            }
        );
#pragma warning restore IDE0090

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(NpgsqlDataSource) ? this._dataSource :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
