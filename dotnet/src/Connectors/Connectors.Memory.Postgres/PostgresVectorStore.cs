// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using Microsoft.Extensions.VectorData;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Represents a vector store implementation using PostgreSQL.
/// </summary>
public class PostgresVectorStore : IVectorStore
{
    private readonly NpgsqlDataSource? _dataSource;

    internal PostgresVectorStoreOptions Options { get; }
    internal IPostgresVectorStoreDbClient PostgresClient { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="options">Optional configuration options for this class</param>
    public PostgresVectorStore(NpgsqlDataSource dataSource, PostgresVectorStoreOptions? options = default)
    {
        this._dataSource = dataSource;
        this.Options = options ?? new PostgresVectorStoreOptions();
        this.PostgresClient = new PostgresVectorStoreDbClient(this._dataSource, this.Options.Schema);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="postgresDbClient">An instance of <see cref="IPostgresDbClient"/>.</param>
    /// <param name="options">Optional configuration options for this class</param>
    internal PostgresVectorStore(IPostgresVectorStoreDbClient postgresDbClient, PostgresVectorStoreOptions? options = default)
    {
        this.PostgresClient = postgresDbClient;
        this.Options = options ?? new PostgresVectorStoreOptions();
    }

    /// <inheritdoc />
    public virtual IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "ListCollectionNames";
        return PostgresVectorStoreUtils.WrapAsyncEnumerableAsync(
            this.PostgresClient.GetTablesAsync(cancellationToken),
            OperationName
        );
    }

    /// <inheritdoc />
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
        if (!PostgresConstants.SupportedKeyTypes.Contains(typeof(TKey)))
        {
            throw new NotSupportedException($"Unsupported key type: {typeof(TKey)}");
        }

#pragma warning disable CS0618 // IPostgresVectorStoreRecordCollectionFactory is obsolete
        if (this.Options.VectorStoreCollectionFactory is not null)
        {
            return this.Options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this.PostgresClient.DataSource, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        var recordCollection = new PostgresVectorStoreRecordCollection<TKey, TRecord>(
            this,
            name,
            new PostgresVectorStoreRecordCollectionOptions<TRecord>() { Schema = this.Options.Schema, VectorStoreRecordDefinition = vectorStoreRecordDefinition }
        );

        return recordCollection as IVectorStoreRecordCollection<TKey, TRecord> ?? throw new InvalidOperationException("Failed to cast record collection.");
    }
}
