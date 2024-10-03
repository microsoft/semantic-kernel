// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Service for storing and retrieving vector records, that uses SQLite as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class SqliteVectorStoreRecordCollection<TRecord> :
    IVectorStoreRecordCollection<ulong, TRecord>,
    IVectorStoreRecordCollection<string, TRecord>
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "SQLite";

    /// <summary><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</summary>
    private readonly SqliteConnection _connection;

    /// <summary>The mapper to use when mapping between the consumer data model and the SQLite record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;

    /// <summary>Command builder for queries in SQLite database.</summary>
    private readonly SqliteVectorStoreCollectionCommandBuilder _commandBuilder;

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

    /// <summary>SQLite extension name for vector search operations.</summary>
    private readonly string _vectorSearchExtensionName;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="connection"><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</param>
    /// <param name="collectionName">The name of the collection/table that this <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="vectorSearchExtensionName">SQLite extension name for vector search operations.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStoreRecordCollection(
        SqliteConnection connection,
        string collectionName,
        string vectorSearchExtensionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(connection);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(vectorSearchExtensionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), customMapperSupplied: false, SqliteConstants.SupportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._connection = connection;
        this.CollectionName = collectionName;
        this._vectorSearchExtensionName = vectorSearchExtensionName;

        // Using prefix for vector table name to avoid name collisions.
        this._dataTableName = this.CollectionName;
        this._vectorTableName = $"vec_{this._dataTableName}";

        var collectionOptions = options ?? new();
        this._propertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), collectionOptions.VectorStoreRecordDefinition, new()
        {
            RequiresAtLeastOneVector = false,
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = true
        });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(SqliteConstants.SupportedKeyTypes);
        this._propertyReader.VerifyDataProperties(SqliteConstants.SupportedDataTypes, supportEnumerable: false);
        this._propertyReader.VerifyVectorProperties(SqliteConstants.SupportedVectorTypes);

        this._vectorPropertiesExist = this._propertyReader.VectorProperties.Count > 0;

        this._dataTableProperties = new(() => [this._propertyReader.KeyProperty, .. this._propertyReader.DataProperties]);
        this._vectorTableProperties = new(() => [this._propertyReader.KeyProperty, .. this._propertyReader.VectorProperties]);

        this._dataTableStoragePropertyNames = new(() => [this._propertyReader.KeyPropertyStoragePropertyName, .. this._propertyReader.DataPropertyStoragePropertyNames]);
        this._vectorTableStoragePropertyNames = new(() => [this._propertyReader.KeyPropertyStoragePropertyName, .. this._propertyReader.VectorPropertyStoragePropertyNames]);

        this._mapper = InitializeMapper(this._propertyReader, options);

        this._commandBuilder = new SqliteVectorStoreCollectionCommandBuilder(this._connection);
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "TableCount";

        using var command = this._commandBuilder.BuildTableCountCommand(this._dataTableName);

        var result = await this
            .RunOperationAsync(OperationName, () => command.ExecuteScalarAsync(cancellationToken))
            .ConfigureAwait(false);

        long? count = result is not null ? (long)result : null;

        var collectionExists = count > 0;

        return collectionExists;
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.InternalCreateCollectionAsync(ifNotExists: false, cancellationToken);
    }

    /// <inheritdoc />
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.InternalCreateCollectionAsync(ifNotExists: true, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        List<Task> tasks = [this.DropTableAsync(this._dataTableName, cancellationToken)];

        if (this._vectorPropertiesExist)
        {
            tasks.Add(this.DropTableAsync(this._vectorTableName, cancellationToken));
        }

        return Task.WhenAll(tasks);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    #region Implementation of IVectorStoreRecordCollection<ulong, TRecord>

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(ulong key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return await this.InternalGetBatchAsync([key], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<ulong> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var record in this.InternalGetBatchAsync(keys, options, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public async Task<ulong> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var key = await this.InternalUpsertBatchAsync<ulong?>([record], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        return key ?? throw new VectorStoreOperationException("Error occurred during upsert operation.");
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ulong> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var key in this.InternalUpsertBatchAsync<ulong?>(records, options, cancellationToken).ConfigureAwait(false))
        {
            if (key.HasValue)
            {
                yield return key.Value;
            }
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(ulong key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteBatchAsync([key], options, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<ulong> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteBatchAsync(keys, options, cancellationToken);
    }

    #endregion

    #region Implementation of IVectorStoreRecordCollection<string, TRecord>

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return await this.InternalGetBatchAsync([key], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var record in this.InternalGetBatchAsync(keys, options, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteBatchAsync([key], options, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteBatchAsync(keys, options, cancellationToken);
    }

    /// <inheritdoc />
    async Task<string> IVectorStoreRecordCollection<string, TRecord>.UpsertAsync(TRecord record, UpsertRecordOptions? options, CancellationToken cancellationToken)
    {
        var key = await this.InternalUpsertBatchAsync<string>([record], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        return key ?? throw new VectorStoreOperationException("Error occurred during upsert operation.");
    }

    /// <inheritdoc />
    async IAsyncEnumerable<string> IVectorStoreRecordCollection<string, TRecord>.UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var key in this.InternalUpsertBatchAsync<string>(records, options, cancellationToken).ConfigureAwait(false))
        {
            if (key is not null)
            {
                yield return key;
            }
        }
    }

    #endregion

    #region private

    private Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        List<SqliteColumn> dataTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(
            this._dataTableProperties.Value,
            this._propertyReader.StoragePropertyNamesMap);

        List<Task> tasks = [this.CreateTableAsync(
            this._dataTableName,
            dataTableColumns,
            ifNotExists,
            cancellationToken)];

        if (this._vectorPropertiesExist)
        {
            List<SqliteColumn> vectorTableColumns = SqliteVectorStoreRecordPropertyMapping.GetColumns(
                this._vectorTableProperties.Value,
                this._propertyReader.StoragePropertyNamesMap);

            tasks.Add(this.CreateVirtualTableAsync(
                this._vectorTableName,
                vectorTableColumns,
                ifNotExists,
                this._vectorSearchExtensionName,
                cancellationToken));
        }

        return Task.WhenAll(tasks);
    }

    private Task<int> CreateTableAsync(string tableName, List<SqliteColumn> columns, bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateTable";

        using var command = this._commandBuilder.BuildCreateTableCommand(tableName, columns, ifNotExists);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> CreateVirtualTableAsync(string tableName, List<SqliteColumn> columns, bool ifNotExists, string extensionName, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateVirtualTable";

        using var command = this._commandBuilder.BuildCreateVirtualTableCommand(tableName, columns, ifNotExists, extensionName);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> DropTableAsync(string tableName, CancellationToken cancellationToken)
    {
        const string OperationName = "DropTable";

        using var command = this._commandBuilder.BuildDropTableCommand(tableName);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private async IAsyncEnumerable<TRecord> InternalGetBatchAsync<TKey>(
        IEnumerable<TKey> keys,
        GetRecordOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(keys);

        const string OperationName = "Select";

        bool includeVectors = options?.IncludeVectors is true && this._vectorPropertiesExist;

        SqliteCommand command;
        List<VectorStoreRecordProperty> properties = [this._propertyReader.KeyProperty, .. this._propertyReader.DataProperties];
        List<TKey> keysList = keys.ToList();

        if (includeVectors)
        {
            command = this._commandBuilder.BuildSelectLeftJoinCommand(
                this._dataTableName,
                this._vectorTableName,
                this._propertyReader.KeyPropertyStoragePropertyName,
                this._dataTableStoragePropertyNames.Value,
                this._propertyReader.VectorPropertyStoragePropertyNames,
                keysList);

            properties.AddRange(this._propertyReader.VectorProperties);
        }
        else
        {
            command = this._commandBuilder.BuildSelectCommand(
                this._dataTableName,
                this._propertyReader.KeyPropertyStoragePropertyName,
                this._dataTableStoragePropertyNames.Value,
                keysList);
        }

        using (command)
        {
            using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                var storageModel = new Dictionary<string, object?>();

                foreach (var property in properties)
                {
                    var propertyName = this._propertyReader.StoragePropertyNamesMap[property.DataModelPropertyName];
                    var propertyType = property.PropertyType;
                    var propertyValue = SqliteVectorStoreRecordPropertyMapping.GetPropertyValue(reader, propertyName, propertyType);

                    storageModel.Add(propertyName, propertyValue);
                }

                yield return VectorStoreErrorHandler.RunModelConversion(
                    DatabaseName,
                    this.CollectionName,
                    OperationName,
                    () => this._mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors }));
            }
        }
    }

    private async IAsyncEnumerable<TKey?> InternalUpsertBatchAsync<TKey>(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        const string OperationName = "Upsert";

        var keyStoragePropertyName = this._propertyReader.KeyPropertyStoragePropertyName;

        var storageModels = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record))).ToList();

        if (this._vectorPropertiesExist)
        {
            // Upsert operation is not supported for vector virtual tables, deleting previous vector records first.
            var keys = storageModels.Select(model => (TKey)model[keyStoragePropertyName]!).ToList();

            using var vectorDeleteCommand = this._commandBuilder.BuildDeleteCommand<TKey>(
                this._vectorTableName,
                keyStoragePropertyName,
                keys);

            await vectorDeleteCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);

            using var vectorInsertOrReplaceCommand = this._commandBuilder.BuildInsertCommand(
                this._vectorTableName,
                keyStoragePropertyName,
                this._vectorTableStoragePropertyNames.Value,
                storageModels);

            await vectorInsertOrReplaceCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        using var dataCommand = this._commandBuilder.BuildInsertCommand(
                this._dataTableName,
                keyStoragePropertyName,
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

    private Task InternalDeleteBatchAsync<TKey>(
        IEnumerable<TKey> keys,
        DeleteRecordOptions? options,
        CancellationToken cancellationToken)
    {
        const string OperationName = "Delete";

        var tasks = new List<Task>();
        var keysList = keys.ToList();

        if (this._vectorPropertiesExist)
        {
            using var vectorCommand = this._commandBuilder.BuildDeleteCommand(
                this._vectorTableName,
                this._propertyReader.KeyPropertyStoragePropertyName,
                keysList);

            tasks.Add(this.RunOperationAsync(OperationName, () => vectorCommand.ExecuteNonQueryAsync(cancellationToken)));
        }

        using var dataCommand = this._commandBuilder.BuildDeleteCommand(
            this._dataTableName,
            this._propertyReader.KeyPropertyStoragePropertyName,
            keysList);

        tasks.Add(this.RunOperationAsync(OperationName, () => dataCommand.ExecuteNonQueryAsync(cancellationToken)));

        return Task.WhenAll(tasks);
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

    private static IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> InitializeMapper(
        VectorStoreRecordPropertyReader propertyReader,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options)
    {
        if (options?.DictionaryCustomMapper is not null)
        {
            return options.DictionaryCustomMapper;
        }

        return new SqliteVectorStoreRecordMapper<TRecord>(propertyReader);
    }

    #endregion
}
