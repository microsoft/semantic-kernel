// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Service for storing and retrieving vector records, that uses SQLite as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be <see cref="string"/>, <see cref="int"/> or <see cref="long"/>.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class SqliteCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</summary>
    private readonly string _connectionString;

    /// <summary>The mapper to use when mapping between the consumer data model and the SQLite record.</summary>
    private readonly SqliteMapper<TRecord> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>Flag which indicates whether vector properties exist in the consumer data model.</summary>
    private readonly bool _vectorPropertiesExist;

    /// <summary>The storage name of the key property.</summary>
    private readonly string _keyStorageName;

    /// <summary>Table name in SQLite for data properties.</summary>
    private readonly string _dataTableName;

    /// <summary>Table name in SQLite for vector properties.</summary>
    private readonly string _vectorTableName;

    /// <inheritdoc />
    public override string Name { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="name">The name of the collection/table that this <see cref="SqliteCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate SqliteDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate SqliteDynamicCollection instead")]
    public SqliteCollection(
        string connectionString,
        string name,
        SqliteCollectionOptions? options = default)
        : this(
            connectionString,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(SqliteDynamicCollection)))
                : new SqliteModelBuilder().Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator),
            options)
    {
    }

    internal SqliteCollection(string connectionString, string name, Func<SqliteCollectionOptions, CollectionModel> modelFactory, SqliteCollectionOptions? options)
    {
        // Verify.
        Verify.NotNull(connectionString);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(int) && typeof(TKey) != typeof(long) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string, int and long keys are supported.");
        }

        options ??= SqliteCollectionOptions.Default;

        // Assign.
        this._connectionString = connectionString;
        this.Name = name;
        this._model = modelFactory(options);

        // Escape both table names before exposing them to anything that may build SQL commands.
        this._dataTableName = name.EscapeIdentifier();
        this._vectorTableName = GetVectorTableName(name, options).EscapeIdentifier();

        this._vectorPropertiesExist = this._model.VectorProperties.Count > 0;

        // Populate some collections of properties
        this._keyStorageName = this._model.KeyProperty.StorageName;
        this._mapper = new SqliteMapper<TRecord>(this._model);

        var connectionStringBuilder = new SqliteConnectionStringBuilder(connectionString);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = SqliteConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.DataSource,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public override async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "TableCount";

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = SqliteCommandBuilder.BuildTableCountCommand(connection, this._dataTableName);

        var result = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteScalarAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        long count = result is not null ? (long)result : 0;

        return count > 0;
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalCreateCollectionAsync(connection, ifNotExists: true, cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
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
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        const string LimitPropertyName = "k";

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        ReadOnlyMemory<float> vector = searchValue switch
        {
            ReadOnlyMemory<float> r => r,
            float[] f => new ReadOnlyMemory<float>(f),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), SqliteModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

        var mappedArray = SqlitePropertyMapping.MapVectorForStorageModel(vector);

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

        await foreach (var record in this.EnumerateAndMapSearchResultsAsync(
            conditions,
            extraWhereFilter,
            extraParameters,
            options,
            cancellationToken)
            .ConfigureAwait(false))
        {
            yield return record;
        }
    }

    #endregion Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, FilteredRecordRetrievalOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        SqliteFilterTranslator translator = new(this._model, filter);
        translator.Translate(appendWhere: false);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        using var command = options.IncludeVectors
            ? SqliteCommandBuilder.BuildSelectInnerJoinCommand(
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
                skip: options.Skip)
            : SqliteCommandBuilder.BuildSelectDataCommand(
                connection,
                this._dataTableName,
                this._model,
                conditions: [],
                filterOptions: options,
                translator.Clause.ToString(),
                translator.Parameters,
                top: top,
                skip: options.Skip);

        const string OperationName = "Get";

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            cancellationToken).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(reader, options.IncludeVectors);
        }
    }

    /// <inheritdoc />
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
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
    public override async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, RecordRetrievalOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding<float>>>? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (SqliteModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding<float>>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = [await floatTask.ConfigureAwait(false)];
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        await this.InternalUpsertBatchAsync(connection, [record], generatedEmbeddings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding<float>>>? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (SqliteModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
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
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding<float>>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        await this.InternalUpsertBatchAsync(connection, records, generatedEmbeddings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var condition = new SqliteWhereEqualsCondition(this._keyStorageName, key);

        await this.InternalDeleteBatchAsync(connection, condition, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
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
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    #region private

    private async ValueTask<SqliteConnection> GetConnectionAsync(CancellationToken cancellationToken = default)
    {
        var connection = new SqliteConnection(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        connection.LoadVector();
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
        using var command = SqliteCommandBuilder.BuildSelectInnerJoinCommand<TRecord>(
            connection,
            this._vectorTableName,
            this._dataTableName,
            this._keyStorageName,
            this._model,
            conditions,
            includeDistance: true,
            extraWhereFilter: extraWhereFilter,
            extraParameters: extraParameters);

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        for (var recordCounter = 0; await reader.ReadAsync(cancellationToken).ConfigureAwait(false); recordCounter++)
        {
            if (recordCounter >= searchOptions.Skip)
            {
                var score = SqlitePropertyMapping.GetPropertyValue<double>(reader, SqliteCommandBuilder.DistancePropertyName);
                var record = this._mapper.MapFromStorageToDataModel(reader, searchOptions.IncludeVectors);

                yield return new VectorSearchResult<TRecord>(record, score);
            }
        }
    }

    private async Task InternalCreateCollectionAsync(SqliteConnection connection, bool ifNotExists, CancellationToken cancellationToken)
    {
        List<SqliteColumn> dataTableColumns = SqlitePropertyMapping.GetColumns(this._model.Properties, data: true);

        await this.CreateTableAsync(connection, this._dataTableName, dataTableColumns, ifNotExists, cancellationToken)
            .ConfigureAwait(false);

        if (this._vectorPropertiesExist)
        {
            List<SqliteColumn> vectorTableColumns = SqlitePropertyMapping.GetColumns(this._model.Properties, data: false);

            await this.CreateVirtualTableAsync(connection, this._vectorTableName, vectorTableColumns, ifNotExists, cancellationToken)
                .ConfigureAwait(false);
        }
    }

    private Task<int> CreateTableAsync(SqliteConnection connection, string tableName, List<SqliteColumn> columns, bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateTable";

        using var command = SqliteCommandBuilder.BuildCreateTableCommand(connection, tableName, columns, ifNotExists);

        return connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken);
    }

    private Task<int> CreateVirtualTableAsync(SqliteConnection connection, string tableName, List<SqliteColumn> columns, bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateVirtualTable";

        using var command = SqliteCommandBuilder.BuildCreateVirtualTableCommand(connection, tableName, columns, ifNotExists);

        return connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken);
    }

    private Task<int> DropTableAsync(SqliteConnection connection, string tableName, CancellationToken cancellationToken)
    {
        const string OperationName = "DropTable";

        using var command = SqliteCommandBuilder.BuildDropTableCommand(connection, tableName);

        return connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken);
    }

    private async IAsyncEnumerable<TRecord> InternalGetBatchAsync(
        SqliteConnection connection,
        SqliteWhereCondition condition,
        RecordRetrievalOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "Select";

        bool includeVectors = options?.IncludeVectors is true && this._vectorPropertiesExist;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var command = includeVectors
            ? SqliteCommandBuilder.BuildSelectInnerJoinCommand<TRecord>(
                connection,
                this._vectorTableName,
                this._dataTableName,
                this._keyStorageName,
                this._model,
                [condition],
                includeDistance: false)
            : SqliteCommandBuilder.BuildSelectDataCommand<TRecord>(
                connection,
                this._dataTableName,
                this._model,
                [condition]);

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            OperationName,
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(reader, includeVectors);
        }
    }

    private async Task InternalUpsertBatchAsync(
        SqliteConnection connection,
        IEnumerable<TRecord> records,
        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding<float>>>? generatedEmbeddings,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        if (this._vectorPropertiesExist)
        {
            // We're going to have to traverse the records multiple times, so materialize the enumerable if needed.
            var recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

            if (recordsList.Count == 0)
            {
                return;
            }

            records = recordsList;

            var keyProperty = this._model.KeyProperty;
            var keys = recordsList.Select(r => keyProperty.GetValueAsObject(r)!).ToList();

            // Deleting vector records first since current version of vector search extension
            // doesn't support Upsert operation, only Delete/Insert.
            using var vectorDeleteCommand = SqliteCommandBuilder.BuildDeleteCommand(
                connection,
                this._vectorTableName,
                [new SqliteWhereInCondition(this._keyStorageName, keys)]);

            await connection.ExecuteWithErrorHandlingAsync(
                this._collectionMetadata,
                "VectorDelete",
                () => vectorDeleteCommand.ExecuteNonQueryAsync(cancellationToken),
                cancellationToken).ConfigureAwait(false);

            using var vectorInsertCommand = SqliteCommandBuilder.BuildInsertCommand(
                connection,
                this._vectorTableName,
                this._keyStorageName,
                this._model,
                records,
                generatedEmbeddings,
                data: false);

            await connection.ExecuteWithErrorHandlingAsync(
                this._collectionMetadata,
                "VectorInsert",
                () => vectorInsertCommand.ExecuteNonQueryAsync(cancellationToken),
                cancellationToken).ConfigureAwait(false);
        }

        using var dataCommand = SqliteCommandBuilder.BuildInsertCommand(
            connection,
            this._dataTableName,
            this._keyStorageName,
            this._model,
            records,
            generatedEmbeddings,
            data: true,
            replaceIfExists: true);

        using var reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "updateData",
            () => dataCommand.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            var key = reader.GetFieldValue<TKey>(0);

            // TODO: Inject the generated keys into the record for autogenerated keys.

            await reader.NextResultAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private Task InternalDeleteBatchAsync(SqliteConnection connection, SqliteWhereCondition condition, CancellationToken cancellationToken)
    {
        var tasks = new List<Task>();

        if (this._vectorPropertiesExist)
        {
            using var vectorCommand = SqliteCommandBuilder.BuildDeleteCommand(
                connection,
                this._vectorTableName,
                [condition]);

            tasks.Add(connection.ExecuteWithErrorHandlingAsync(
                this._collectionMetadata,
                "VectorDelete",
                () => vectorCommand.ExecuteNonQueryAsync(cancellationToken),
                cancellationToken));
        }

        using var dataCommand = SqliteCommandBuilder.BuildDeleteCommand(
            connection,
            this._dataTableName,
            [condition]);

        tasks.Add(connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "DataDelete",
            () => dataCommand.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken));

        return Task.WhenAll(tasks);
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
        SqliteCollectionOptions options)
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
