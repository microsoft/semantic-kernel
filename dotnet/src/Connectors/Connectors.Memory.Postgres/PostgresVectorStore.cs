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
public sealed class PostgresVectorStore : IVectorStore
{
    private readonly IPostgresVectorStoreDbClient _postgresClient;
    private readonly NpgsqlDataSource? _dataSource;
    private readonly PostgresVectorStoreOptions _options;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreRecordKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="options">Optional configuration options for this class</param>
    public PostgresVectorStore(NpgsqlDataSource dataSource, PostgresVectorStoreOptions? options = default)
    {
        this._dataSource = dataSource;
        this._options = options ?? new PostgresVectorStoreOptions();
        this._postgresClient = new PostgresVectorStoreDbClient(this._dataSource, this._options.Schema);

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
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return PostgresVectorStoreUtils.WrapAsyncEnumerableAsync(
            this._postgresClient.GetTablesAsync(cancellationToken),
            "ListCollectionNames",
            this._metadata.VectorStoreName
        );
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
    {
#pragma warning disable CS0618 // IPostgresVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._postgresClient.DataSource, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        var recordCollection = new PostgresVectorStoreRecordCollection<TKey, TRecord>(
            this._postgresClient,
            name,
            new PostgresVectorStoreRecordCollectionOptions<TRecord>()
            {
                Schema = this._options.Schema,
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator,
            }
        );

        return recordCollection as IVectorStoreRecordCollection<TKey, TRecord> ?? throw new InvalidOperationException("Failed to cast record collection.");
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
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
