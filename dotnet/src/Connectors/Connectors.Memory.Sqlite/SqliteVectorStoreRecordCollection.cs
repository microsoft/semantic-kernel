// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

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
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;
#pragma warning restore CS0618

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>Flag which indicates whether vector properties exist in the consumer data model.</summary>
    private readonly bool _vectorPropertiesExist;

    /// <summary>The storage name of the key property.</summary>
    private readonly string _keyStorageName;

    /// <summary>Collection of properties to operate in SQLite data table.</summary>
    private readonly List<VectorStoreRecordPropertyModel> _dataTableProperties = [];

    /// <summary>Collection of properties to operate in SQLite vector table.</summary>
    private readonly List<VectorStoreRecordPropertyModel> _vectorTableProperties = [];

    /// <summary>Collection of property names to operate in SQLite data table.</summary>
    private readonly List<string> _dataTableStoragePropertyNames = [];

    /// <summary>Collection of property names to operate in SQLite vector table.</summary>
    private readonly List<string> _vectorTableStoragePropertyNames = [];

    /// <summary>Table name in SQLite for data properties.</summary>
    private readonly string _dataTableName;

    /// <summary>Table name in SQLite for vector properties.</summary>
    private readonly string _vectorTableName;

    /// <summary>The sqlite_vec extension name to use.</summary>
    private readonly string _vectorSearchExtensionName;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="collectionName">The name of the collection/table that this <see cref="SqliteVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStoreRecordCollection(
        string connectionString,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(connectionString);
        Verify.NotNullOrWhiteSpace(collectionName);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(ulong) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException($"Only {nameof(String)} and {nameof(UInt64)} keys are supported (and object for dynamic mapping).");
        }

        // Assign.
        this._connectionString = connectionString;
        this.CollectionName = collectionName;
        this._options = options ?? new();
        this._vectorSearchExtensionName = this._options.VectorSearchExtensionName ?? SqliteConstants.VectorSearchExtensionName;

        this._dataTableName = this.CollectionName;
        this._vectorTableName = GetVectorTableName(this._dataTableName, this._options);

        this._model = new VectorStoreRecordModelBuilder(SqliteConstants.ModelBuildingOptions)
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition);

        this._vectorPropertiesExist = this._model.VectorProperties.Count > 0;

        // Populate some collections of properties
        this._keyStorageName = this._model.KeyProperty.StorageName;

        foreach (var property in this._model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    this._dataTableProperties.Add(keyProperty);
                    this._vectorTableProperties.Add(keyProperty);
                    this._dataTableStoragePropertyNames.Add(keyProperty.StorageName);
                    this._vectorTableStoragePropertyNames.Add(keyProperty.StorageName);
                    break;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    this._dataTableProperties.Add(dataProperty);
                    this._dataTableStoragePropertyNames.Add(dataProperty.StorageName);
                    break;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    this._vectorTableProperties.Add(vectorProperty);
                    this._vectorTableStoragePropertyNames.Add(vectorProperty.StorageName);
                    break;

                default:
                    throw new UnreachableException();
            }
        }
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
        this._mapper = this._options.DictionaryCustomMapper ?? new SqliteVectorStoreRecordMapper<TRecord>(this._model);
#pragma warning restore CS0618

        var connectionStringBuilder = new SqliteConnectionStringBuilder(connectionString);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = SqliteConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.DataSource,
            CollectionName = collectionName
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

    /// <inheritdoc />
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
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

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(searchOptions);

        var mappedArray = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = top + searchOptions.Skip;

        var conditions = new List<SqliteWhereCondition>()
        {
            new SqliteWhereMatchCondition(vectorProperty.StorageName, mappedArray),
            new SqliteWhereEqualsCondition(LimitPropertyName, limit)
        };

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        string? extraWhereFilter = null;
        Dictionary<string, object>? extraParameters = null;

        if (searchOptions.OldFilter is not null)
        {
            if (searchOptions.Filter is not null)
            {
                throw new ArgumentException("Either Filter or OldFilter can be specified, but not both");
            }

            // Old filter, we translate it to a list of SqliteWhereCondition, and merge these into the conditions we already have
            var filterConditions = this.GetFilterConditions(searchOptions.OldFilter, this._dataTableName);

            if (filterConditions is { Count: > 0 })
            {
                conditions.AddRange(filterConditions);
            }
        }
        else if (searchOptions.Filter is not null)
        {
            SqliteFilterTranslator translator = new(this._model, searchOptions.Filter);
            translator.Translate(appendWhere: false);
            extraWhereFilter = translator.Clause.ToString();
            extraParameters = translator.Parameters;
        }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        var vectorSearchResults = new VectorSearchResults<TRecord>(this.EnumerateAndMapSearchResultsAsync(
            conditions,
            extraWhereFilter,
            extraParameters,
            searchOptions,
            cancellationToken));

        return Task.FromResult(vectorSearchResults);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        SqliteFilterTranslator translator = new(this._model, filter);
        translator.Translate(appendWhere: false);

        IReadOnlyList<VectorStoreRecordPropertyModel> properties = options.IncludeVectors
            ? this._model.Properties
            : [this._model.KeyProperty, .. this._model.DataProperties];

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectWhereCommand(
            this._model,
            connection,
            top,
            options,
            this._dataTableName,
            this._model.Properties,
            translator.Clause.ToString(),
            translator.Parameters);

        using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return this.GetAndMapRecord(
                "Get",
                reader,
                properties,
                options.IncludeVectors);
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
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        Verify.NotNull(keys);

        var keysList = keys.Cast<object>().ToList();

        Verify.True(keysList.Count > 0, "Number of provided keys should be greater than zero.");

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
        const string OperationName = "Upsert";

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            SqliteConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        var key = storageModel[this._keyStorageName];

        Verify.NotNull(key);

        var condition = new SqliteWhereEqualsCondition(this._keyStorageName, key);

        var upsertedRecordKey = await this.InternalUpsertBatchAsync(connection, [storageModel], condition, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        return upsertedRecordKey ?? throw new VectorStoreOperationException("Error occurred during upsert operation.");
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TKey> UpsertAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertBatch";

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var storageModels = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
            SqliteConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record))).ToList();

        var keys = storageModels.Select(model => model[this._keyStorageName]!).ToList();

        var condition = new SqliteWhereInCondition(this._keyStorageName, keys);

        await foreach (var record in this.InternalUpsertBatchAsync(connection, storageModels, condition, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
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

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        var keysList = keys.Cast<object>().ToList();

        Verify.True(keysList.Count > 0, "Number of provided keys should be greater than zero.");

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
        const string DistancePropertyName = "distance";

        var leftTableProperties = new List<string> { DistancePropertyName };

        List<VectorStoreRecordPropertyModel> properties = [this._model.KeyProperty, .. this._model.DataProperties];

        if (searchOptions.IncludeVectors)
        {
            foreach (var property in this._model.VectorProperties)
            {
                leftTableProperties.Add(property.StorageName);
            }
            properties.AddRange(this._model.VectorProperties);
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand(
            connection,
            this._vectorTableName,
            this._dataTableName,
            this._keyStorageName,
            leftTableProperties,
            this._dataTableStoragePropertyNames,
            conditions,
            extraWhereFilter,
            extraParameters,
            DistancePropertyName);

        using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        for (var recordCounter = 0; await reader.ReadAsync(cancellationToken).ConfigureAwait(false); recordCounter++)
        {
            if (recordCounter >= searchOptions.Skip)
            {
                var score = SqliteVectorStoreRecordPropertyMapping.GetPropertyValue<double>(reader, DistancePropertyName);

                var record = this.GetAndMapRecord(
                    OperationName,
                    reader,
                    properties,
                    searchOptions.IncludeVectors);

                yield return new VectorSearchResult<TRecord>(record, score);
            }
        }
    }

    private async Task InternalCreateCollectionAsync(SqliteConnection connection, bool ifNotExists, CancellationToken cancellationToken)
    {
        List<SqliteColumn> dataTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(this._dataTableProperties);

        await this.CreateTableAsync(connection, this._dataTableName, dataTableColumns, ifNotExists, cancellationToken)
            .ConfigureAwait(false);

        if (this._vectorPropertiesExist)
        {
            var extensionName = !string.IsNullOrWhiteSpace(this._options.VectorSearchExtensionName) ?
                this._options.VectorSearchExtensionName :
                SqliteConstants.VectorSearchExtensionName;

            List<SqliteColumn> vectorTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(this._vectorTableProperties);

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
        List<VectorStoreRecordPropertyModel> properties = [this._model.KeyProperty, .. this._model.DataProperties];

        if (includeVectors)
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand(
                connection,
                this._dataTableName,
                this._vectorTableName,
                this._keyStorageName,
                this._dataTableStoragePropertyNames,
                this._model.VectorProperties.Select(p => p.StorageName).ToList(),
                [condition]);

            properties.AddRange(this._model.VectorProperties);
        }
        else
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectCommand(
                connection,
                this._dataTableName,
                this._dataTableStoragePropertyNames,
                [condition]);
        }

        using (command)
        {
            using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.GetAndMapRecord(
                    OperationName,
                    reader,
                    properties,
                    includeVectors);
            }
        }
    }

    private async IAsyncEnumerable<TKey> InternalUpsertBatchAsync(
        SqliteConnection connection,
        List<Dictionary<string, object?>> storageModels,
        SqliteWhereCondition condition,
        [EnumeratorCancellation] CancellationToken cancellationToken)
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
                this._vectorTableStoragePropertyNames,
                storageModels);

            await vectorInsertCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        using var dataCommand = SqliteVectorStoreCollectionCommandBuilder.BuildInsertCommand(
            connection,
            this._dataTableName,
            this._keyStorageName,
            this._dataTableStoragePropertyNames,
            storageModels,
            replaceIfExists: true);

        using var reader = await dataCommand.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            var key = reader.GetFieldValue<TKey?>(0);

            if (key is not null)
            {
                yield return key;
            }

            await reader.NextResultAsync(cancellationToken).ConfigureAwait(false);
        }
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
        bool includeVectors)
    {
        var storageModel = new Dictionary<string, object?>();

        foreach (var property in properties)
        {
            var propertyValue = SqliteVectorStoreRecordPropertyMapping.GetPropertyValue(reader, property.StorageName, property.Type);
            storageModel.Add(property.StorageName, propertyValue);
        }

        return VectorStoreErrorHandler.RunModelConversion(
            SqliteConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.CollectionName,
            operationName,
            () => this._mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors }));
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
                CollectionName = this.CollectionName,
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
