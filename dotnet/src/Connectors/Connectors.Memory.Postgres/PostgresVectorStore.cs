// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Represents a vector store implementation using PostgreSQL.
/// </summary>
public sealed class PostgresVectorStore : VectorStore
{
    private readonly IPostgresVectorStoreDbClient _postgresClient;
    private readonly PostgresVectorStoreOptions _options;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="options">Optional configuration options for this class</param>
    public PostgresVectorStore(NpgsqlDataSource dataSource, PostgresVectorStoreOptions? options = default)
    {
        this._options = options ?? new PostgresVectorStoreOptions();
        this._postgresClient = new PostgresDbClient(dataSource, this._options.Schema);

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
        this._options = options ?? new PostgresVectorStoreOptions();

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

    /// <inheritdoc />
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        => new PostgresCollection<TKey, TRecord>(
            this._postgresClient,
            name,
            new PostgresCollectionOptions<TRecord>()
            {
                Schema = this._options.Schema,
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator,
            }
        );

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
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
