// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Class for accessing the list of collections in a SQLite vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public class SqliteVectorStore : IVectorStore
{
    /// <summary>The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</summary>
    private readonly string _connectionString;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly SqliteVectorStoreOptions _options;

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
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
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

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(ulong))
        {
            throw new NotSupportedException($"Only {nameof(String)} and {nameof(UInt64)} keys are supported.");
        }

        var recordCollection = new SqliteVectorStoreRecordCollection<TRecord>(
            this._connectionString,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                VectorSearchExtensionName = this._options.VectorSearchExtensionName,
                VectorVirtualTableName = this._options.VectorVirtualTableName
            }) as IVectorStoreRecordCollection<TKey, TRecord>;

        return recordCollection!;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
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
}
