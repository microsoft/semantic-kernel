// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
public sealed class SqliteVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</summary>
    private readonly string _connectionString;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly SqliteVectorStoreOptions _options;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

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

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
#if NET8_0_OR_GREATER
    public override SqliteCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#endif
        => new SqliteCollection<TKey, TRecord>(
            this._connectionString,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                VectorSearchExtensionName = this._options.VectorSearchExtensionName,
                VectorVirtualTableName = this._options.VectorVirtualTableName,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            });
#pragma warning restore IDE0090

    /// <inheritdoc />
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "ListCollectionNames";
        const string TablePropertyName = "name";
        const string Query = $"SELECT {TablePropertyName} FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';";

        using var connection = new SqliteConnection(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();

        command.CommandText = Query;

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._metadata,
            OperationName,
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(
            this._metadata,
            OperationName,
            cancellationToken).ConfigureAwait(false))
        {
            var ordinal = reader.GetOrdinal(TablePropertyName);
            yield return reader.GetString(ordinal);
        }
    }

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
