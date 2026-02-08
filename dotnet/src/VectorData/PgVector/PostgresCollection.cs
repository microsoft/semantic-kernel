// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a collection of vector store records in a Postgres database.
/// </summary>
/// <typeparam name="TKey">The type of the key.</typeparam>
/// <typeparam name="TRecord">The type of the record.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class PostgresCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>, IKeywordHybridSearchable<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : class
{
    /// <inheritdoc />
    public override string Name { get; }

    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>Data source used to interact with the database.</summary>
    private readonly NpgsqlDataSource _dataSource;
    private readonly NpgsqlDataSourceArc? _dataSourceArc;
    private readonly string _databaseName;

    /// <summary>The database schema.</summary>
    private readonly string _schema;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly PostgresMapper<TRecord> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultHybridSearchOptions = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="dataSource">The data source to use for connecting to the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="ownsDataSource">A value indicating whether <paramref name="dataSource"/> is disposed when the collection is disposed.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead")]
    public PostgresCollection(NpgsqlDataSource dataSource, string name, bool ownsDataSource, PostgresCollectionOptions? options = default)
        : this(dataSource, ownsDataSource ? new NpgsqlDataSourceArc(dataSource) : null, name, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead")]
    public PostgresCollection(string connectionString, string name, PostgresCollectionOptions? options = default)
        : this(PostgresUtils.CreateDataSource(connectionString), name, ownsDataSource: true, options)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
    }

    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    internal PostgresCollection(NpgsqlDataSource dataSource, NpgsqlDataSourceArc? dataSourceArc, string name, PostgresCollectionOptions? options)
        : this(
            dataSource,
            dataSourceArc,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(PostgresDynamicCollection)))
                : new PostgresModelBuilder().Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator),
            options)
    {
    }

    internal PostgresCollection(NpgsqlDataSource dataSource, NpgsqlDataSourceArc? dataSourceArc, string name, Func<PostgresCollectionOptions, CollectionModel> modelFactory, PostgresCollectionOptions? options)
    {
        Verify.NotNullOrWhiteSpace(name);

        options ??= PostgresCollectionOptions.Default;

        this.Name = name;
        this._model = modelFactory(options);
        this._mapper = new PostgresMapper<TRecord>(this._model);

        this._dataSource = dataSource;
        this._dataSourceArc = dataSourceArc;
        this._databaseName = new NpgsqlConnectionStringBuilder(dataSource.ConnectionString).Database!;
        this._schema = options.Schema;

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
            VectorStoreName = this._databaseName,
            CollectionName = name
        };

        // Don't add any lines after this - an exception thrown afterwards would leave the reference count wrongly incremented.
        this._dataSourceArc?.IncrementReferenceCount();
    }

    /// <inheritdoc />
    protected override void Dispose(bool disposing)
    {
        this._dataSourceArc?.Dispose();
        base.Dispose(disposing);
    }

    /// <inheritdoc/>
    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("DoesTableExists", async () =>
        {
            NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

            await using (connection)
            using (var command = connection.CreateCommand())
            {
                PostgresSqlBuilder.BuildDoesTableExistCommand(command, this._schema, this.Name);
                using NpgsqlDataReader dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

                if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
                {
                    return dataReader.GetString(dataReader.GetOrdinal("table_name")) == this.Name;
                }

                return false;
            }
        });

    /// <inheritdoc/>
    public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("EnsureCollectionExists", () =>
            this.InternalCreateCollectionAsync(true, cancellationToken));
    }

    /// <inheritdoc/>
    public override async Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
    {
        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildDropTableCommand(command, this._schema, this.Name);

        await this.RunOperationAsync("DeleteCollection", () => command.ExecuteNonQueryAsync()).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
        => this.UpsertAsync([record], cancellationToken);

    /// <inheritdoc/>
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);
        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (PostgresModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // Materialize the records' enumerable if needed, to prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return;
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = await floatTask.ConfigureAwait(false);
            }
#if NET
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<Half>>(records, cancellationToken, out var halfTask))
            {
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = await halfTask.ConfigureAwait(false);
            }
#endif
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, BinaryEmbedding>(records, cancellationToken, out var binaryTask))
            {
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = await binaryTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var batch = connection.CreateBatch();

        // If key auto-generation is enabled, we'll need to enumerate over the records multiple times:
        // once to generate the upsert batch, and again to populate the retrieved keys into the records.
        // To prevent multiple enumeration of the input enumerable, we materialize it here if needed.
        if (this._model.KeyProperty.IsAutoGenerated && recordsList is null)
        {
            recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

            if (recordsList.Count == 0)
            {
                return;
            }

            records = recordsList;
        }

        if (PostgresSqlBuilder.BuildUpsertCommand<TKey>(batch, this._schema, this.Name, this._model, records, generatedEmbeddings))
        {
            await this.RunOperationAsync("Upsert", async () =>
            {
                var reader = await batch.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
                try
                {
                    var keyProperty = this._model.KeyProperty;
                    if (keyProperty.IsAutoGenerated)
                    {
                        int? keyOrdinal = null;

                        foreach (var record in recordsList!)
                        {
                            if (Equals(keyProperty.GetValueAsObject(record), default(TKey)))
                            {
                                keyOrdinal ??= reader.GetOrdinal(keyProperty.StorageName);

                                await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
                                var keyValue = reader.GetFieldValue<TKey>(keyOrdinal.Value);
                                this._model.KeyProperty.SetValue<TKey>(record, keyValue);
                                await reader.NextResultAsync(cancellationToken).ConfigureAwait(false);
                            }
                        }
                    }
                }
                finally
                {
                    await reader.DisposeAsync().ConfigureAwait(false);
                }
            }).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildGetCommand(command, this._schema, this.Name, this._model, key, includeVectors);

        return await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            operationName: "Get",
            async () =>
            {
                using NpgsqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
                await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
                return reader.HasRows
                    ? this._mapper.MapFromStorageToDataModel(reader, includeVectors)
                    : null;
            },
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        RecordRetrievalOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetBatch";

        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        List<TKey> listOfKeys = keys.ToList();
        if (listOfKeys.Count == 0)
        {
            yield break;
        }

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildGetBatchCommand(command, this._schema, this.Name, this._model, listOfKeys, includeVectors);

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(this._collectionMetadata, OperationName, cancellationToken).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(reader, includeVectors);
        }
    }

    /// <inheritdoc/>
    public override async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildDeleteCommand(command, this._schema, this.Name, this._model.KeyProperty.StorageName, key);

        await this.RunOperationAsync("Delete", () => command.ExecuteNonQueryAsync(cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var listOfKeys = keys.ToList();
        if (listOfKeys.Count == 0)
        {
            return;
        }

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildDeleteBatchCommand(command, this._schema, this.Name, this._model.KeyProperty.StorageName, listOfKeys);

        await this.RunOperationAsync("DeleteBatch", () => command.ExecuteNonQueryAsync(cancellationToken)).ConfigureAwait(false);
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
        var pgVector = await this.ConvertSearchInputToVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = top + options.Skip;

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildGetNearestMatchCommand(command, this._schema, this.Name, this._model, vectorProperty, pgVector,
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
            options.OldFilter,
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
            options.Filter, options.Skip, options.IncludeVectors, top, options.ScoreThreshold);

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "Search",
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(this._collectionMetadata, "Search", cancellationToken).ConfigureAwait(false))
        {
            yield return new VectorSearchResult<TRecord>(
                this._mapper.MapFromStorageToDataModel(reader, options.IncludeVectors),
                reader.GetDouble(reader.GetOrdinal(PostgresConstants.DistanceColumnName)));
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(
        TInput searchValue,
        ICollection<string> keywords,
        int top,
        HybridSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        Verify.NotNull(searchValue);
        Verify.NotNull(keywords);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultHybridSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var textProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);
        var pgVector = await this.ConvertSearchInputToVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildHybridSearchCommand(command, this._schema, this.Name, this._model, vectorProperty, textProperty, pgVector, keywords,
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
            options.OldFilter,
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
            options.Filter, options.Skip, options.IncludeVectors, top, options.ScoreThreshold);

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "HybridSearch",
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(this._collectionMetadata, "HybridSearch", cancellationToken).ConfigureAwait(false))
        {
            yield return new VectorSearchResult<TRecord>(
                this._mapper.MapFromStorageToDataModel(reader, options.IncludeVectors),
                reader.GetDouble(reader.GetOrdinal(PostgresConstants.DistanceColumnName)));
        }
    }

    #endregion Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(
        Expression<Func<TRecord, bool>> filter,
        int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        using var connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = connection.CreateCommand();
        PostgresSqlBuilder.BuildSelectWhereCommand(command, this._schema, this.Name, this._model, filter, top, options);
        using NpgsqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(this._collectionMetadata, "Get", cancellationToken).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(reader, options.IncludeVectors);
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(NpgsqlDataSource) ? this._dataSource :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    private async Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken = default)
    {
        // Execute the commands in a transaction.
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var pgVersion = connection.PostgreSqlVersion;

            // Prepare the SQL commands.
            using var batch = connection.CreateBatch();

            batch.BatchCommands.Add(
                new NpgsqlBatchCommand(PostgresSqlBuilder.BuildCreateTableSql(this._schema, this.Name, this._model, pgVersion, ifNotExists)));

            foreach (var (column, kind, function, isVector, isFullText, fullTextLanguage) in PostgresPropertyMapping.GetIndexInfo(this._model.Properties))
            {
                batch.BatchCommands.Add(
                    new NpgsqlBatchCommand(
                        PostgresSqlBuilder.BuildCreateIndexSql(this._schema, this.Name, column, kind, function, isVector, isFullText, fullTextLanguage, ifNotExists)));
            }

            await batch.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private Task RunOperationAsync(string operationName, Func<Task> operation)
        => VectorStoreErrorHandler.RunOperationAsync<NpgsqlException>(
            this._collectionMetadata,
            operationName,
            operation);

    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
        => VectorStoreErrorHandler.RunOperationAsync<T, NpgsqlException>(
            this._collectionMetadata,
            operationName,
            operation);

    /// <summary>
    /// Converts a search input value to a PostgreSQL vector representation, generating embeddings if necessary.
    /// </summary>
    private async Task<object> ConvertSearchInputToVectorAsync<TInput>(TInput searchValue, VectorPropertyModel vectorProperty, CancellationToken cancellationToken)
        where TInput : notnull
    {
        object vector = searchValue switch
        {
            // Dense float32
            ReadOnlyMemory<float> r => r,
            float[] f => new ReadOnlyMemory<float>(f),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

#if NET
            // Dense float16
            ReadOnlyMemory<Half> r => r,
            Half[] f => new ReadOnlyMemory<Half>(f),
            Embedding<Half> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<Half>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),
#endif

            // Dense Binary
            BitArray b => b,
            BinaryEmbedding e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, BinaryEmbedding> generator
                => await generator.GenerateAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            // Sparse
            SparseVector sv => sv,
            // TODO: Add a PG-specific SparseVectorEmbedding type

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), PostgresModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

        var pgVector = PostgresPropertyMapping.MapVectorForStorageModel(vector);
        Verify.NotNull(pgVector);
        return pgVector;
    }
}
