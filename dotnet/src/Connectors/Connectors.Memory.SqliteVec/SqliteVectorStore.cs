// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

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

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>Custom virtual table name to store vectors.</summary>
    private readonly string? _vectorVirtualTableName;

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStore"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStore(string connectionString, SqliteVectorStoreOptions? options = default)
    {
        Verify.NotNull(connectionString);

        this._connectionString = connectionString;

        options ??= SqliteVectorStoreOptions.Default;
        this._vectorVirtualTableName = options.VectorVirtualTableName;
        this._embeddingGenerator = options.EmbeddingGenerator;

        var connectionStringBuilder = new SqliteConnectionStringBuilder(connectionString);

        this._metadata = new()
        {
            VectorStoreSystemName = SqliteConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.DataSource
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresDynamicCode("This overload of GetCollection() is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
    [RequiresUnreferencedCode("This overload of GetCollecttion() is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
#if NET8_0_OR_GREATER
    public override SqliteCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new SqliteCollection<TKey, TRecord>(
                this._connectionString,
                name,
                new()
                {
                    Definition = definition,
                    VectorVirtualTableName = this._vectorVirtualTableName,
                    EmbeddingGenerator = this._embeddingGenerator
                });

    /// <inheritdoc />
#if NET8_0_OR_GREATER
    public override SqliteDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new SqliteDynamicCollection(
            this._connectionString,
            name,
            new()
            {
                Definition = definition,
                VectorVirtualTableName = this._vectorVirtualTableName,
                EmbeddingGenerator = this._embeddingGenerator
            }
        );
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
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.EnsureCollectionDeletedAsync(cancellationToken);
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
