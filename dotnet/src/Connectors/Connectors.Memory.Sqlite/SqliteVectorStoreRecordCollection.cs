// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Service for storing and retrieving vector records, that uses SQLite as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be <see cref="string"/> or <see cref="ulong"/>, or <see cref="object"/> for dynamic mapping.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class SqliteVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    /// <summary>The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</summary>
    private readonly string _connectionString;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly SqliteVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The mapper to use when mapping between the consumer data model and the SQLite record.</summary>
    private readonly SqliteVectorStoreRecordMapper<TRecord> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>Flag which indicates whether vector properties exist in the consumer data model.</summary>
    private readonly bool _vectorPropertiesExist;

    /// <summary>The storage name of the key property.</summary>
    private readonly string _keyStorageName;

    /// <summary>Table name in SQLite for data properties.</summary>
    private readonly string _dataTableName;

    /// <summary>Table name in SQLite for vector properties.</summary>
    private readonly string _vectorTableName;

    /// <summary>The sqlite_vec extension name to use.</summary>
    private readonly string _vectorSearchExtensionName;

    /// <inheritdoc />
    public string Name { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="name">The name of the collection/table that this <see cref="SqliteVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStoreRecordCollection(
        string connectionString,
        string name,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(connectionString);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(ulong) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException($"Only {nameof(String)} and {nameof(UInt64)} keys are supported (and object for dynamic mapping).");
        }

        // Assign.
        this._connectionString = connectionString;
        this.Name = name;
        this._options = options ?? new();
        this._vectorSearchExtensionName = this._options.VectorSearchExtensionName ?? SqliteConstants.VectorSearchExtensionName;

        // Escape both table names before exposing them to anything that may build SQL commands.
        this._dataTableName = name.EscapeIdentifier();
        this._vectorTableName = GetVectorTableName(name, this._options).EscapeIdentifier();

        this._model = new VectorStoreRecordModelBuilder(SqliteConstants.ModelBuildingOptions)
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, this._options.EmbeddingGenerator);

        this._vectorPropertiesExist = this._model.VectorProperties.Count > 0;

        // Populate some collections of properties
        this._keyStorageName = this._model.KeyProperty.StorageName;
        this._mapper = new SqliteVectorStoreRecordMapper<TRecord>(this._model);

        var connectionStringBuilder = new SqliteConnectionStringBuilder(connectionString);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = SqliteConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.DataSource,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "TableCount";

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildTableCountCommand(connection, this._dataTableName);

        var result = await this
            .RunOperationAsync(OperationName, () => command.ExecuteScalarAsync(cancellationToken))
            .ConfigureAwait(false);

        long count = result is not null ? (long)result : 0;

        return count > 0;
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalCreateCollectionAsync(connection, ifNotExists: false, cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalCreateCollectionAsync(connection, ifNotExists: true, cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        await this.DropTableAsync(connection, this._dataTableName, cancellationToken).ConfigureAwait(false);

        if (this._vectorPropertiesExist)
        {
            await this.DropTableAsync(connection, this._vectorTableName, cancellationToken).ConfigureAwait(false);
        }
    }

    #region Search

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
                var embedding = await generator.GenerateAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    SqliteConstants.SupportedVectorTypes.Contains(typeof(TInput))
                        ? string.Format(VectorDataStrings.EmbeddingTypePassedToSearchAsync)
                        : string.Format(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType, typeof(TInput).Name, vectorProperty.EmbeddingGenerator.GetType().Name));
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        string operationName,
        VectorSearchOptions<TRecord> options,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        const string LimitPropertyName = "k";

        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        var vectorType = vector.GetType();
        if (!SqliteConstants.SupportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the SQLite connector. " +
                $"Supported types are: {string.Join(", ", SqliteConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var mappedArray = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = top + options.Skip;

        var conditions = new List<SqliteWhereCondition>()
        {
            new SqliteWhereMatchCondition(vectorProperty.StorageName, mappedArray),
            new SqliteWhereEqualsCondition(LimitPropertyName, limit)
        };

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        string? extraWhereFilter = null;
        Dictionary<string, object>? extraParameters = null;

        if (options.OldFilter is not null)
        {
            if (options.Filter is not null)
            {
                throw new ArgumentException("Either Filter or OldFilter can be specified, but not both");
            }

            // Old filter, we translate it to a list of SqliteWhereCondition, and merge these into the conditions we already have
            var filterConditions = this.GetFilterConditions(options.OldFilter, this._dataTableName);

            if (filterConditions is { Count: > 0 })
            {
                conditions.AddRange(filterConditions);
            }
        }
        else if (options.Filter is not null)
        {
            SqliteFilterTranslator translator = new(this._model, options.Filter);
            translator.Translate(appendWhere: false);
            extraWhereFilter = translator.Clause.ToString();
            extraParameters = translator.Parameters;
        }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        return this.EnumerateAndMapSearchResultsAsync(
            conditions,
            extraWhereFilter,
            extraParameters,
            options,
            cancellationToken);
    }

    /// <inheritdoc />
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    #endregion Search

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        SqliteFilterTranslator translator = new(this._model, filter);
        translator.Translate(appendWhere: false);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        DbCommand? command = null;

        if (options.IncludeVectors)
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand(
                connection,
                this._vectorTableName,
                this._dataTableName,
                this._keyStorageName,
                this._model,
                conditions: [],
                includeDistance: false,
                filterOptions: options,
                translator.Clause.ToString(),
                translator.Parameters,
                top: top,
                skip: options.Skip);
        }
        else
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectDataCommand(
                connection,
                this._dataTableName,
                this._model,
                conditions: [],
                filterOptions: options,
                translator.Clause.ToString(),
                translator.Parameters,
                top: top,
                skip: options.Skip);
        }

        using (command)
        {
            StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors };
            using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.GetAndMapRecord(
                    "Get",
                    reader,
                    this._model.Properties,
                    mapperOptions);
            }
        }
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var condition = new SqliteWhereEqualsCondition(this._keyStorageName, key)
        {
            TableName = this._dataTableName
        };

        return await this.InternalGetBatchAsync(connection, condition, options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);
        var keysList = keys.Cast<object>().ToList();
        if (keysList.Count == 0)
        {
            yield break;
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var condition = new SqliteWhereInCondition(this._keyStorageName, keysList)
        {
            TableName = this._dataTableName
        };

        await foreach (var record in this.InternalGetBatchAsync(connection, condition, options, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        const string OperationName = "Upsert";

        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>, ReadOnlyMemory<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = [await floatTask.ConfigureAwait(false)];
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            SqliteConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record, recordIndex: 0, generatedEmbeddings));

        var key = storageModel[this._keyStorageName];

        Verify.NotNull(key);

        var condition = new SqliteWhereEqualsCondition(this._keyStorageName, key);

        var upsertedRecordKeys = await this.InternalUpsertBatchAsync(connection, [storageModel], condition, cancellationToken)
            .ConfigureAwait(false);

        return upsertedRecordKeys.Single() ?? throw new VectorStoreOperationException("Error occurred during upsert operation.");
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        const string OperationName = "UpsertBatch";

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return [];
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var storageModels = VectorStoreErrorHandler.RunModelConversion(
            SqliteConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            OperationName,
            () => records.Select((r, i) => this._mapper.MapFromDataToStorageModel(r, i, generatedEmbeddings)).ToList());

        if (storageModels.Count == 0)
        {
            return [];
        }

        var keys = storageModels.Select(model => model[this._keyStorageName]!).ToList();

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        var condition = new SqliteWhereInCondition(this._keyStorageName, keys);

        return await this.InternalUpsertBatchAsync(connection, storageModels, condition, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var condition = new SqliteWhereEqualsCondition(this._keyStorageName, key);

        await this.InternalDeleteBatchAsync(connection, condition, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);
        var keysList = keys.Cast<object>().ToList();
        if (keysList.Count == 0)
        {
            return;
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var condition = new SqliteWhereInCondition(
            this._keyStorageName,
            keysList);

        await this.InternalDeleteBatchAsync(connection, condition, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    #region private

    private async ValueTask<SqliteConnection> GetConnectionAsync(CancellationToken cancellationToken = default)
    {
        var connection = new SqliteConnection(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        connection.LoadExtension(this._vectorSearchExtensionName);
        return connection;
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> EnumerateAndMapSearchResultsAsync(
        List<SqliteWhereCondition> conditions,
        string? extraWhereFilter,
        Dictionary<string, object>? extraParameters,
        VectorSearchOptions<TRecord> searchOptions,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "VectorizedSearch";

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand<TRecord>(
            connection,
            this._vectorTableName,
            this._dataTableName,
            this._keyStorageName,
            this._model,
            conditions,
            includeDistance: true,
            extraWhereFilter: extraWhereFilter,
            extraParameters: extraParameters);

        using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = searchOptions.IncludeVectors };
        for (var recordCounter = 0; await reader.ReadAsync(cancellationToken).ConfigureAwait(false); recordCounter++)
        {
            if (recordCounter >= searchOptions.Skip)
            {
                var score = SqliteVectorStoreRecordPropertyMapping.GetPropertyValue<double>(reader, SqliteVectorStoreCollectionCommandBuilder.DistancePropertyName);

                var record = this.GetAndMapRecord(
                    OperationName,
                    reader,
                    this._model.Properties,
                    mapperOptions);

                yield return new VectorSearchResult<TRecord>(record, score);
            }
        }
    }

    private async Task InternalCreateCollectionAsync(SqliteConnection connection, bool ifNotExists, CancellationToken cancellationToken)
    {
        List<SqliteColumn> dataTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(this._model.Properties, data: true);

        await this.CreateTableAsync(connection, this._dataTableName, dataTableColumns, ifNotExists, cancellationToken)
            .ConfigureAwait(false);

        if (this._vectorPropertiesExist)
        {
            var extensionName = !string.IsNullOrWhiteSpace(this._options.VectorSearchExtensionName) ?
                this._options.VectorSearchExtensionName :
                SqliteConstants.VectorSearchExtensionName;

            List<SqliteColumn> vectorTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(this._model.Properties, data: false);

            await this.CreateVirtualTableAsync(connection, this._vectorTableName, vectorTableColumns, ifNotExists, extensionName!, cancellationToken)
                .ConfigureAwait(false);
        }
    }

    private Task<int> CreateTableAsync(SqliteConnection connection, string tableName, List<SqliteColumn> columns, bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateTable";

        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildCreateTableCommand(connection, tableName, columns, ifNotExists);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> CreateVirtualTableAsync(SqliteConnection connection, string tableName, List<SqliteColumn> columns, bool ifNotExists, string extensionName, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateVirtualTable";

        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildCreateVirtualTableCommand(connection, tableName, columns, ifNotExists, extensionName);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> DropTableAsync(SqliteConnection connection, string tableName, CancellationToken cancellationToken)
    {
        const string OperationName = "DropTable";

        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildDropTableCommand(connection, tableName);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private async IAsyncEnumerable<TRecord> InternalGetBatchAsync(
        SqliteConnection connection,
        SqliteWhereCondition condition,
        GetRecordOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "Select";

        bool includeVectors = options?.IncludeVectors is true && this._vectorPropertiesExist;

        DbCommand command;

        if (includeVectors)
        {
            if (this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
            {
                throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
            }

            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand<TRecord>(
                connection,
                this._vectorTableName,
                this._dataTableName,
                this._keyStorageName,
                this._model,
                [condition],
                includeDistance: false);
        }
        else
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectDataCommand<TRecord>(
                connection,
                this._dataTableName,
                this._model,
                [condition]);
        }

        using (command)
        {
            StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = includeVectors };

            using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.GetAndMapRecord(
                    OperationName,
                    reader,
                    this._model.Properties,
                    mapperOptions);
            }
        }
    }

    private async Task<IReadOnlyList<TKey>> InternalUpsertBatchAsync(
        SqliteConnection connection,
        List<Dictionary<string, object?>> storageModels,
        SqliteWhereCondition condition,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(storageModels);
        Verify.True(storageModels.Count > 0, "Number of provided records should be greater than zero.");

        if (this._vectorPropertiesExist)
        {
            // Deleting vector records first since current version of vector search extension
            // doesn't support Upsert operation, only Delete/Insert.
            using var vectorDeleteCommand = SqliteVectorStoreCollectionCommandBuilder.BuildDeleteCommand(
                connection,
                this._vectorTableName,
                [condition]);

            await vectorDeleteCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);

            using var vectorInsertCommand = SqliteVectorStoreCollectionCommandBuilder.BuildInsertCommand(
                connection,
                this._vectorTableName,
                this._keyStorageName,
                this._model.Properties,
                storageModels,
                data: false);

            await vectorInsertCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        using var dataCommand = SqliteVectorStoreCollectionCommandBuilder.BuildInsertCommand(
            connection,
            this._dataTableName,
            this._keyStorageName,
            this._model.Properties,
            storageModels,
            data: true,
            replaceIfExists: true);

        using var reader = await dataCommand.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        var keys = new List<TKey>();

        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            var key = reader.GetFieldValue<TKey?>(0);

            if (key is not null)
            {
                keys.Add(key);
            }

            await reader.NextResultAsync(cancellationToken).ConfigureAwait(false);
        }

        return keys;
    }

    private Task InternalDeleteBatchAsync(SqliteConnection connection, SqliteWhereCondition condition, CancellationToken cancellationToken)
    {
        const string OperationName = "Delete";

        var tasks = new List<Task>();

        if (this._vectorPropertiesExist)
        {
            using var vectorCommand = SqliteVectorStoreCollectionCommandBuilder.BuildDeleteCommand(
                connection,
                this._vectorTableName,
                [condition]);

            tasks.Add(this.RunOperationAsync(OperationName, () => vectorCommand.ExecuteNonQueryAsync(cancellationToken)));
        }

        using var dataCommand = SqliteVectorStoreCollectionCommandBuilder.BuildDeleteCommand(
            connection,
            this._dataTableName,
            [condition]);

        tasks.Add(this.RunOperationAsync(OperationName, () => dataCommand.ExecuteNonQueryAsync(cancellationToken)));

        return Task.WhenAll(tasks);
    }

    private TRecord GetAndMapRecord(
        string operationName,
        DbDataReader reader,
        IReadOnlyList<VectorStoreRecordPropertyModel> properties,
        StorageToDataModelMapperOptions options)
    {
        var storageModel = new Dictionary<string, object?>();

        foreach (var property in properties)
        {
            if (options.IncludeVectors || property is not VectorStoreRecordVectorPropertyModel)
            {
                var propertyValue = SqliteVectorStoreRecordPropertyMapping.GetPropertyValue(reader, property.StorageName, property.Type);
                storageModel.Add(property.StorageName, propertyValue);
            }
        }

        return VectorStoreErrorHandler.RunModelConversion(
            SqliteConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            operationName,
            () => this._mapper.MapFromStorageToDataModel(storageModel, options));
    }

    private async Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = SqliteConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    private List<SqliteWhereCondition>? GetFilterConditions(VectorSearchFilter? filter, string? tableName = null)
    {
        var filterClauses = filter?.FilterClauses.ToList();

        if (filterClauses is not { Count: > 0 })
        {
            return null;
        }

        var conditions = new List<SqliteWhereCondition>();

        foreach (var filterClause in filterClauses)
        {
            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                if (!this._model.PropertyMap.TryGetValue(equalToFilterClause.FieldName, out var property))
                {
                    throw new InvalidOperationException($"Property name '{equalToFilterClause.FieldName}' provided as part of the filter clause is not a valid property name.");
                }

                conditions.Add(new SqliteWhereEqualsCondition(property.StorageName, equalToFilterClause.Value)
                {
                    TableName = tableName
                });
            }
            else
            {
                throw new NotSupportedException(
                    $"Unsupported filter clause type '{filterClause.GetType().Name}'. " +
                    $"Supported filter clause types are: {string.Join(", ", [
                        nameof(EqualToFilterClause)])}");
            }
        }

        return conditions;
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

    /// <summary>
    /// Gets vector table name.
    /// </summary>
    /// <remarks>
    /// If custom vector table name is not provided, default one will be generated with a prefix to avoid name collisions.
    /// </remarks>
    private static string GetVectorTableName(
        string dataTableName,
        SqliteVectorStoreRecordCollectionOptions<TRecord> options)
    {
        const string DefaultVirtualTableNamePrefix = "vec_";

        if (!string.IsNullOrWhiteSpace(options.VectorVirtualTableName))
        {
            return options.VectorVirtualTableName!;
        }

        return $"{DefaultVirtualTableNamePrefix}{dataTableName}";
    }

    #endregion
}
