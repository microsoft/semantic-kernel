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

    /// <summary>A <see cref="HashSet{T}"/> of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(ulong),
        typeof(string)
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(ulong),
        typeof(ulong?),
        typeof(short),
        typeof(short?),
        typeof(ushort),
        typeof(ushort?),
        typeof(string),
        typeof(bool),
        typeof(bool?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(byte[]),
        typeof(DateTime),
        typeof(DateTime?),
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that vector properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
    ];

    /// <summary><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</summary>
    private readonly SqliteConnection _connection;

    /// <summary>The key property of the current storage model.</summary>
    private readonly VectorStoreRecordKeyProperty _keyProperty;

    /// <summary>Collection of record data properties.</summary>
    private readonly List<VectorStoreRecordDataProperty> _dataProperties;

    /// <summary>Collection of record vector properties.</summary>
    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>A dictionary that maps from a property name to the storage name.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = [];

    /// <summary>The mapper to use when mapping between the consumer data model and the SQLite record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;

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
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), customMapperSupplied: false, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._connection = connection;
        this.CollectionName = collectionName;

        var vectorStoreRecordDefinition = options?.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), supportsMultipleVectors: true);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(properties.DataProperties, s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");

        this._keyProperty = properties.KeyProperty;
        this._dataProperties = properties.DataProperties;
        this._vectorProperties = properties.VectorProperties;

        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties);

        this._mapper = this.InitializeMapper(options);
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "TableCount";

        var command = SqliteVectorStoreCollectionCommandBuilder.BuildTableCountCommand(
            this._connection,
            this.CollectionName);

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
        return this.CreateTableAsync(ifNotExists: false, cancellationToken);
    }

    /// <inheritdoc />
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.CreateTableAsync(ifNotExists: true, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DropTable";

        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildDropTableCommand(
            this._connection,
            this.CollectionName);

        return this.RunOperationAsync(OperationName, () => command.ExecuteNonQueryAsync(cancellationToken));
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

    private Task<int> CreateTableAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        const string OperationName = "CreateTable";

        using var command = SqliteVectorStoreCollectionCommandBuilder.BuildCreateTableCommand(
            this._connection,
            this.CollectionName,
            this._keyProperty,
            this._dataProperties,
            this._storagePropertyNames,
            ifNotExists);

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

    private async Task RunOperationAsync(string operationName, Func<Task> operation)
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
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

    private IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> InitializeMapper(SqliteVectorStoreRecordCollectionOptions<TRecord>? options)
    {
        if (options?.DictionaryCustomMapper is not null)
        {
            return options.DictionaryCustomMapper;
        }

        return new SqliteVectorStoreRecordMapper<TRecord>();
    }

    #endregion
}
