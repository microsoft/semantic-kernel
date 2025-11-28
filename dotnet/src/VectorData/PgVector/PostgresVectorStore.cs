// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a vector store implementation using PostgreSQL.
/// </summary>
public sealed class PostgresVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>Data source used to interact with the database.</summary>
    private readonly NpgsqlDataSource _dataSource;
    private readonly NpgsqlDataSourceArc? _dataSourceArc;
    private readonly string _databaseName;

    /// <summary>The database schema.</summary>
    private readonly string _schema;

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="ownsDataSource">A value indicating whether <paramref name="dataSource"/> is disposed when this instance of <see cref="PostgresVectorStore"/> is disposed.</param>
    /// <param name="options">Optional configuration options for this class</param>
    public PostgresVectorStore(NpgsqlDataSource dataSource, bool ownsDataSource, PostgresVectorStoreOptions? options = default)
    {
        Verify.NotNull(dataSource);

        this._schema = options?.Schema ?? PostgresVectorStoreOptions.Default.Schema;
        this._embeddingGenerator = options?.EmbeddingGenerator;
        this._dataSource = dataSource;
        this._dataSourceArc = ownsDataSource ? new NpgsqlDataSourceArc(dataSource) : null;
        this._databaseName = new NpgsqlConnectionStringBuilder(dataSource.ConnectionString).Database!;

        this._metadata = new()
        {
            VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
            VectorStoreName = this._databaseName
        };
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStore"/> class.
    /// </summary>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresVectorStore(string connectionString, PostgresVectorStoreOptions? options = default)
#pragma warning disable CA2000 // Dispose objects before losing scope
        : this(PostgresUtils.CreateDataSource(connectionString), ownsDataSource: true, options)
#pragma warning restore CA2000 // Dispose objects before losing scope
    {
    }

    /// <inheritdoc/>
    protected override void Dispose(bool disposing)
    {
        this._dataSourceArc?.Dispose();
        base.Dispose(disposing);
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return PostgresUtils.WrapAsyncEnumerableAsync(
            GetTablesAsync(cancellationToken),
            "ListCollectionNames",
            this._metadata);

        async IAsyncEnumerable<string> GetTablesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

            await using (connection)
            using (var command = connection.CreateCommand())
            {
                PostgresSqlBuilder.BuildGetTablesCommand(command, this._schema);
                using NpgsqlDataReader dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

                while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
                {
                    yield return dataReader.GetString(dataReader.GetOrdinal("table_name"));
                }
            }
        }
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresDynamicCode("This overload of GetCollection() is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
    [RequiresUnreferencedCode("This overload of GetCollecttion() is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
#if NET
    public override PostgresCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new PostgresCollection<TKey, TRecord>(
                this._dataSource,
                this._dataSourceArc,
                name,
                new()
                {
                    Schema = this._schema,
                    Definition = definition,
                    EmbeddingGenerator = this._embeddingGenerator,
                }
            );

    /// <inheritdoc />
#if NET
    public override PostgresDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new PostgresDynamicCollection(
            this._dataSource,
            this._dataSourceArc,
            name,
            new()
            {
                Schema = this._schema,
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator,
            }
        );
#pragma warning restore IDE0090 // Use 'new(...)'

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
            serviceType == typeof(NpgsqlDataSource) ? this._dataSource :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
