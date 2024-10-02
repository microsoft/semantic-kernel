// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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

    /// <summary>The mapper to use when mapping between the consumer data model and the SQLite record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;

    /// <summary>Command builder for queries in SQLite database.</summary>
    private readonly SqliteVectorStoreCollectionCommandBuilder _commandBuilder;

    /// <summary>Flag which indicates whether vector properties exist in the consumer data model.</summary>
    private readonly bool _vectorPropertiesExist;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="connection"><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</param>
    /// <param name="collectionName">The name of the collection/table that this <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public SqliteVectorStoreRecordCollection(
        SqliteConnection connection,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(connection);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), customMapperSupplied: false, SqliteConstants.SupportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this.CollectionName = collectionName;

        var vectorStoreRecordDefinition = options?.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), supportsMultipleVectors: true);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes([properties.KeyProperty], SqliteConstants.SupportedKeyTypes, "Key");
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(properties.DataProperties, SqliteConstants.SupportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(properties.VectorProperties, SqliteConstants.SupportedVectorTypes, "Vector");

        this._vectorPropertiesExist = properties.VectorProperties.Count > 0;

        var storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties);

        this._mapper = InitializeMapper(
            vectorStoreRecordDefinition,
            storagePropertyNames,
            options);

        this._commandBuilder = new SqliteVectorStoreCollectionCommandBuilder(
            this.CollectionName,
            connection,
            properties.KeyProperty,
            properties.DataProperties,
            properties.VectorProperties,
            storagePropertyNames);
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "TableCount";

        var command = this._commandBuilder.BuildTableCountCommand();

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
        List<Task> tasks = [this.DropTableAsync(cancellationToken)];

        if (this._vectorPropertiesExist)
        {
            tasks.Add(this.DropVirtualTableAsync(cancellationToken));
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
    public Task<TRecord?> GetAsync(ulong key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<ulong> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task<ulong> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<ulong> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task DeleteAsync(ulong key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<ulong> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    #endregion

    #region Implementation of IVectorStoreRecordCollection<string, TRecord>

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    Task<string> IVectorStoreRecordCollection<string, TRecord>.UpsertAsync(TRecord record, UpsertRecordOptions? options, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    IAsyncEnumerable<string> IVectorStoreRecordCollection<string, TRecord>.UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }

    #endregion

    #region private

    private Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        List<Task> tasks = [this.CreateTableAsync(ifNotExists, cancellationToken)];

        if (this._vectorPropertiesExist)
        {
            tasks.Add(this.CreateVirtualTableAsync(ifNotExists, cancellationToken));
        }

        return Task.WhenAll(tasks);
    }

    private Task<int> CreateTableAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateTable";

        using var command = this._commandBuilder.BuildCreateTableCommand(ifNotExists);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> CreateVirtualTableAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateVirtualTable";

        using var command = this._commandBuilder.BuildCreateVirtualTableCommand(ifNotExists);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> DropTableAsync(CancellationToken cancellationToken)
    {
        const string OperationName = "DropTable";

        using var command = this._commandBuilder.BuildDropTableCommand();

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
    }

    private Task<int> DropVirtualTableAsync(CancellationToken cancellationToken)
    {
        const string OperationName = "DropVirtualTable";

        using var command = this._commandBuilder.BuildDropVirtualTableCommand();

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
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
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        Dictionary<string, string> storagePropertyNames,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options)
    {
        if (options?.DictionaryCustomMapper is not null)
        {
            return options.DictionaryCustomMapper;
        }

        return new SqliteVectorStoreRecordMapper<TRecord>(
            vectorStoreRecordDefinition,
            storagePropertyNames);
    }

    #endregion
}
