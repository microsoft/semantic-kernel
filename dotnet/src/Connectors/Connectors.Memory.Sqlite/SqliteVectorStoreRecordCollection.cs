// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Service for storing and retrieving vector records, that uses SQLite as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class SqliteVectorStoreRecordCollection<TRecord> :
    IVectorStoreRecordCollection<ulong, TRecord>,
    IVectorStoreRecordCollection<string, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "SQLite";

    /// <summary>The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</summary>
    private readonly string _connectionString;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly SqliteVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The mapper to use when mapping between the consumer data model and the SQLite record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>Contains helpers for reading vector store model properties and their attributes.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>Flag which indicates whether vector properties exist in the consumer data model.</summary>
    private readonly bool _vectorPropertiesExist;

    /// <summary>Collection of properties to operate in SQLite data table.</summary>
    private readonly Lazy<List<VectorStoreRecordProperty>> _dataTableProperties;

    /// <summary>Collection of properties to operate in SQLite vector table.</summary>
    private readonly Lazy<List<VectorStoreRecordProperty>> _vectorTableProperties;

    /// <summary>Collection of property names to operate in SQLite data table.</summary>
    private readonly Lazy<List<string>> _dataTableStoragePropertyNames;

    /// <summary>Collection of property names to operate in SQLite vector table.</summary>
    private readonly Lazy<List<string>> _vectorTableStoragePropertyNames;

    /// <summary>Table name in SQLite for data properties.</summary>
    private readonly string _dataTableName;

    /// <summary>Table name in SQLite for vector properties.</summary>
    private readonly string _vectorTableName;

    /// <summary>The sqlite_vec extension name to use.</summary>
    private readonly string _vectorSearchExtensionName;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="collectionName">The name of the collection/table that this <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStoreRecordCollection(
        string connectionString,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(connectionString);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.DictionaryCustomMapper is not null, SqliteConstants.SupportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._connectionString = connectionString;
        this.CollectionName = collectionName;
        this._options = options ?? new();
        this._vectorSearchExtensionName = this._options.VectorSearchExtensionName ?? SqliteConstants.VectorSearchExtensionName;

        this._dataTableName = this.CollectionName;
        this._vectorTableName = GetVectorTableName(this._dataTableName, this._options);

        this._propertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), this._options.VectorStoreRecordDefinition, new()
        {
            RequiresAtLeastOneVector = false,
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = true
        });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(SqliteConstants.SupportedKeyTypes);

        this._vectorPropertiesExist = this._propertyReader.VectorProperties.Count > 0;

        this._dataTableProperties = new(() => [this._propertyReader.KeyProperty, .. this._propertyReader.DataProperties]);
        this._vectorTableProperties = new(() => [this._propertyReader.KeyProperty, .. this._propertyReader.VectorProperties]);

        this._dataTableStoragePropertyNames = new(() => [this._propertyReader.KeyPropertyStoragePropertyName, .. this._propertyReader.DataPropertyStoragePropertyNames]);
        this._vectorTableStoragePropertyNames = new(() => [this._propertyReader.KeyPropertyStoragePropertyName, .. this._propertyReader.VectorPropertyStoragePropertyNames]);

        this._mapper = this.InitializeMapper();
    }

    /// <inheritdoc />
    public virtual async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
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
    public virtual async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);

        await this.DropTableAsync(connection, this._dataTableName, cancellationToken).ConfigureAwait(false);

        if (this._vectorPropertiesExist)
        {
            await this.DropTableAsync(connection, this._vectorTableName, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        const string LimitPropertyName = "k";

        Verify.NotNull(vector);

        var vectorType = vector.GetType();
        if (!SqliteConstants.SupportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the SQLite connector. " +
                $"Supported types are: {string.Join(", ", SqliteConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(searchOptions);

        var mappedArray = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = searchOptions.Top + searchOptions.Skip;

        var conditions = new List<SqliteWhereCondition>()
        {
            new SqliteWhereMatchCondition(this._propertyReader.GetStoragePropertyName(vectorProperty.DataModelPropertyName), mappedArray),
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
            SqliteFilterTranslator translator = new(this._propertyReader.StoragePropertyNamesMap, searchOptions.Filter);
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

    #region Implementation of IVectorStoreRecordCollection<ulong, TRecord>

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(ulong key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this.InternalGetAsync(connection, key, options, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<ulong> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var keysList = GetKeysAsListOfObjects(keys);
        if (keysList.Count == 0)
        {
            yield break;
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await foreach (var record in this.InternalGetBatchAsync(connection, keysList, options, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public async Task<ulong> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this.InternalUpsertAsync<ulong>(connection, record, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ulong> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await foreach (var record in this.InternalUpsertBatchAsync<ulong>(connection, records, cancellationToken)
                           .ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public async Task DeleteAsync(ulong key, CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalDeleteAsync(connection, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(IEnumerable<ulong> keys, CancellationToken cancellationToken = default)
    {
        var keysList = GetKeysAsListOfObjects(keys);
        if (keysList.Count == 0)
        {
            return;
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalDeleteBatchAsync(connection, keysList, cancellationToken).ConfigureAwait(false);
    }

    #endregion

    #region Implementation of IVectorStoreRecordCollection<string, TRecord>

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this.InternalGetAsync(connection, key, options, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var keysList = GetKeysAsListOfObjects(keys);
        if (keysList.Count == 0)
        {
            yield break;
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await foreach (var record in this.InternalGetBatchAsync(connection, keysList, options, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    async Task<string> IVectorStoreRecordCollection<string, TRecord>.UpsertAsync(TRecord record, CancellationToken cancellationToken)
    {
        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this.InternalUpsertAsync<string>(connection, record, cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    async IAsyncEnumerable<string> IVectorStoreRecordCollection<string, TRecord>.UpsertBatchAsync(
        IEnumerable<TRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await foreach (var record in this.InternalUpsertBatchAsync<string>(connection, records, cancellationToken)
                           .ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public async Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalDeleteAsync(connection, key, cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        var keysList = GetKeysAsListOfObjects(keys);
        if (keysList.Count == 0)
        {
            return;
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this.InternalDeleteBatchAsync(connection, keysList, cancellationToken).ConfigureAwait(false);
    }

    #endregion

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

        List<VectorStoreRecordProperty> properties = [this._propertyReader.KeyProperty, .. this._propertyReader.DataProperties];

        if (searchOptions.IncludeVectors)
        {
            leftTableProperties.AddRange(this._propertyReader.VectorPropertyStoragePropertyNames);
            properties.AddRange(this._propertyReader.VectorProperties);
        }

        using var connection = await this.GetConnectionAsync(cancellationToken).ConfigureAwait(false);
        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand(
            connection,
            this._vectorTableName,
            this._dataTableName,
            this._propertyReader.KeyPropertyStoragePropertyName,
            leftTableProperties,
            this._dataTableStoragePropertyNames.Value,
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

    private Task InternalCreateCollectionAsync(SqliteConnection connection, bool ifNotExists, CancellationToken cancellationToken)
    {
        List<SqliteColumn> dataTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(
            this._dataTableProperties.Value,
            this._propertyReader.StoragePropertyNamesMap);

        List<Task> tasks = [this.CreateTableAsync(
            connection,
            this._dataTableName,
            dataTableColumns,
            ifNotExists,
            cancellationToken)];

        if (this._vectorPropertiesExist)
        {
            var extensionName = !string.IsNullOrWhiteSpace(this._options.VectorSearchExtensionName) ?
                this._options.VectorSearchExtensionName :
                SqliteConstants.VectorSearchExtensionName;

            List<SqliteColumn> vectorTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(
                this._vectorTableProperties.Value,
                this._propertyReader.StoragePropertyNamesMap);

            tasks.Add(this.CreateVirtualTableAsync(
                connection,
                this._vectorTableName,
                vectorTableColumns,
                ifNotExists,
                extensionName!,
                cancellationToken));
        }

        return Task.WhenAll(tasks);
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

    private async Task<TRecord?> InternalGetAsync<TKey>(
        SqliteConnection connection,
        TKey key,
        GetRecordOptions? options,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(key);

        var condition = new SqliteWhereEqualsCondition(this._propertyReader.KeyPropertyStoragePropertyName, key)
        {
            TableName = this._dataTableName
        };

        return await this.InternalGetBatchAsync(connection, condition, options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    private IAsyncEnumerable<TRecord> InternalGetBatchAsync(
        SqliteConnection connection,
        List<object> keysList,
        GetRecordOptions? options,
        CancellationToken cancellationToken)
    {
        var condition = new SqliteWhereInCondition(this._propertyReader.KeyPropertyStoragePropertyName, keysList)
        {
            TableName = this._dataTableName
        };

        return this.InternalGetBatchAsync(connection, condition, options, cancellationToken);
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
        List<VectorStoreRecordProperty> properties = [this._propertyReader.KeyProperty, .. this._propertyReader.DataProperties];

        if (includeVectors)
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectLeftJoinCommand(
                connection,
                this._dataTableName,
                this._vectorTableName,
                this._propertyReader.KeyPropertyStoragePropertyName,
                this._dataTableStoragePropertyNames.Value,
                this._propertyReader.VectorPropertyStoragePropertyNames,
                [condition]);

            properties.AddRange(this._propertyReader.VectorProperties);
        }
        else
        {
            command = SqliteVectorStoreCollectionCommandBuilder.BuildSelectCommand(
                connection,
                this._dataTableName,
                this._dataTableStoragePropertyNames.Value,
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

    private async Task<TKey> InternalUpsertAsync<TKey>(SqliteConnection connection, TRecord record, CancellationToken cancellationToken)
    {
        const string OperationName = "Upsert";

        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        var key = storageModel[this._propertyReader.KeyPropertyStoragePropertyName];

        Verify.NotNull(key);

        var condition = new SqliteWhereEqualsCondition(this._propertyReader.KeyPropertyStoragePropertyName, key);

        var upsertedRecordKey = await this.InternalUpsertBatchAsync<TKey>(connection, [storageModel], condition, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        return upsertedRecordKey ?? throw new VectorStoreOperationException("Error occurred during upsert operation.");
    }

    private IAsyncEnumerable<TKey> InternalUpsertBatchAsync<TKey>(SqliteConnection connection, IEnumerable<TRecord> records, CancellationToken cancellationToken)
    {
        const string OperationName = "UpsertBatch";

        var storageModels = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record))).ToList();

        if (storageModels.Count == 0)
        {
            return AsyncEnumerable.Empty<TKey>();
        }

        var keys = storageModels.Select(model => model[this._propertyReader.KeyPropertyStoragePropertyName]!).ToList();

        var condition = new SqliteWhereInCondition(this._propertyReader.KeyPropertyStoragePropertyName, keys);

        return this.InternalUpsertBatchAsync<TKey>(connection, storageModels, condition, cancellationToken);
    }

    private async IAsyncEnumerable<TKey> InternalUpsertBatchAsync<TKey>(
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
                this._propertyReader.KeyPropertyStoragePropertyName,
                this._vectorTableStoragePropertyNames.Value,
                storageModels);

            await vectorInsertCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        using var dataCommand = SqliteVectorStoreCollectionCommandBuilder.BuildInsertCommand(
            connection,
            this._dataTableName,
            this._propertyReader.KeyPropertyStoragePropertyName,
            this._dataTableStoragePropertyNames.Value,
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

    private Task InternalDeleteAsync<TKey>(SqliteConnection connection, TKey key, CancellationToken cancellationToken)
    {
        var condition = new SqliteWhereEqualsCondition(this._propertyReader.KeyPropertyStoragePropertyName, key);

        return this.InternalDeleteBatchAsync(connection, condition, cancellationToken);
    }

    private Task InternalDeleteBatchAsync(SqliteConnection connection, List<object> keys, CancellationToken cancellationToken)
    {
        var condition = new SqliteWhereInCondition(
            this._propertyReader.KeyPropertyStoragePropertyName,
            keys);

        return this.InternalDeleteBatchAsync(connection, condition, cancellationToken);
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
        List<VectorStoreRecordProperty> properties,
        bool includeVectors)
    {
        var storageModel = new Dictionary<string, object?>();

        foreach (var property in properties)
        {
            var propertyName = this._propertyReader.GetStoragePropertyName(property.DataModelPropertyName);
            var propertyType = property.PropertyType;
            var propertyValue = SqliteVectorStoreRecordPropertyMapping.GetPropertyValue(reader, propertyName, propertyType);

            storageModel.Add(propertyName, propertyValue);
        }

        return VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
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
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

    private IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> InitializeMapper()
    {
        if (this._options.DictionaryCustomMapper is not null)
        {
            return this._options.DictionaryCustomMapper;
        }

        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>) ||
            typeof(TRecord) == typeof(VectorStoreGenericDataModel<ulong>))
        {
            var mapper = new SqliteGenericDataModelMapper(this._propertyReader);
            return (mapper as IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>)!;
        }

        return new SqliteVectorStoreRecordMapper<TRecord>(this._propertyReader);
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
                if (!this._propertyReader.StoragePropertyNamesMap.TryGetValue(equalToFilterClause.FieldName, out var storagePropertyName))
                {
                    throw new InvalidOperationException($"Property name '{equalToFilterClause.FieldName}' provided as part of the filter clause is not a valid property name.");
                }

                conditions.Add(new SqliteWhereEqualsCondition(storagePropertyName, equalToFilterClause.Value)
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

    private static List<object> GetKeysAsListOfObjects<TKey>(IEnumerable<TKey> keys)
    {
        Verify.NotNull(keys);

        return keys.Cast<object>().ToList();
    }
}
