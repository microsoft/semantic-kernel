// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Class for accessing the list of collections in a SQLite vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class SqliteVectorStore : IVectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</summary>
    private readonly string _connectionString;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly SqliteVectorStoreOptions _options;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreRecordKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStore"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStore(string connectionString, SqliteVectorStoreOptions? options = default)
    {
        Verify.NotNull(connectionString);

        this._connectionString = connectionString;
        this._options = options ?? new();

        var connectionStringBuilder = new SqliteConnectionStringBuilder(connectionString);

        this._metadata = new()
        {
            VectorStoreSystemName = SqliteConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.DataSource
        };
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStore"/> class.
    /// </summary>
    /// <param name="connection"><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [Obsolete("Use the constructor that accepts a connection string instead.", error: true)]
    public SqliteVectorStore(
        DbConnection connection,
        SqliteVectorStoreOptions? options = default)
        => throw new InvalidOperationException("Use the constructor that accepts a connection string instead.");

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
    {
#pragma warning disable CS0618 // ISqliteVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(
                this._connectionString,
                name,
                vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        var recordCollection = new SqliteVectorStoreRecordCollection<TKey, TRecord>(
            this._connectionString,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                VectorSearchExtensionName = this._options.VectorSearchExtensionName,
                VectorVirtualTableName = this._options.VectorVirtualTableName,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            }) as IVectorStoreRecordCollection<TKey, TRecord>;

        return recordCollection!;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string TablePropertyName = "name";
        const string Query = $"SELECT {TablePropertyName} FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';";

        using var connection = new SqliteConnection(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();

        command.CommandText = Query;

        using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            var ordinal = reader.GetOrdinal(TablePropertyName);
            yield return reader.GetString(ordinal);
        }
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
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
