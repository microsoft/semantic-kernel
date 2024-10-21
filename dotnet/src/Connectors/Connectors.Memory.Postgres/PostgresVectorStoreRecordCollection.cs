// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Represents a collection of vector store records in a Postgres database.
/// </summary>
/// <typeparam name="TKey">The type of the key.</typeparam>
/// <typeparam name="TRecord">The type of the record.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PostgresVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>, IVectorizableTextSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Postgres";

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>Postgres client that is used to interact with the database.</summary>
    private readonly IPostgresVectorStoreDbClient _client;

    // <summary>Optional configuration options for this class.</summary>
    private readonly PostgresVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="client">The Postgres client used to interact with the database.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresVectorStoreRecordCollection(IPostgresVectorStoreDbClient client, string collectionName, PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(client);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.DictionaryCustomMapper is not null, PostgresConstants.SupportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._client = client;
        this.CollectionName = collectionName;
        this._options = options ?? new PostgresVectorStoreRecordCollectionOptions<TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true,
            });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(PostgresConstants.SupportedKeyTypes);
        this._propertyReader.VerifyDataProperties(PostgresConstants.SupportedDataTypes, supportEnumerable: true);
        this._propertyReader.VerifyVectorProperties(PostgresConstants.SupportedVectorTypes);

        // Resolve mapper.
        // First, if someone has provided a custom mapper, use that.
        // If they didn't provide a custom mapper, and the record type is the generic data model, use the built in mapper for that.
        // Otherwise, don't set the mapper, and we'll default to just using Azure AI Search's built in json serialization and deserialization.
        if (this._options.DictionaryCustomMapper is not null)
        {
            this._mapper = this._options.DictionaryCustomMapper;
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>) || typeof(TRecord) == typeof(VectorStoreGenericDataModel<ulong>))
        {
            this._mapper = (new PostgresGenericDataModelMapper(this._propertyReader) as IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>)!;
        }
        else
        {
            this._mapper = new PostgresVectorStoreRecordMapper<TRecord>(this._propertyReader);
        }
    }

    /// <inheritdoc/>
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return await this._client.DoesTableExistsAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this._client.CreateTableAsync(this.CollectionName, this._propertyReader.RecordDefinition, false, cancellationToken);
    }

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._client.CreateTableAsync(this.CollectionName, this._propertyReader.RecordDefinition, true, cancellationToken);
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this._client.DeleteTableAsync(this.CollectionName, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Upsert";

        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        Verify.NotNull(storageModel);

        var keyObj = storageModel[this._propertyReader.KeyPropertyStoragePropertyName];
        Verify.NotNull(keyObj);
        TKey key = (TKey)keyObj!;

        await this._client.UpsertAsync(this.CollectionName, this._mapper?.MapFromDataToStorageModel(record) ?? throw new InvalidOperationException("Failed to map record to storage model."), this._propertyReader.KeyPropertyStoragePropertyName, cancellationToken).ConfigureAwait(false);
        return key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertBatch";

        var storageModels = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record))).ToList();

        var keys = storageModels.Select(model => model[this._propertyReader.KeyPropertyStoragePropertyName]!).ToList();

        await this._client.UpsertBatchAsync(this.CollectionName, storageModels, this._propertyReader.KeyPropertyStoragePropertyName, cancellationToken).ConfigureAwait(false);

        foreach (var key in keys) { yield return (TKey)key!; }
    }

    /// <inheritdoc/>
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var operationName = "Get";

        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;

        var row = await this._client.GetAsync(this.CollectionName, key, this._propertyReader.RecordDefinition, includeVectors, cancellationToken).ConfigureAwait(false);

        if (row is null) { return default; }

        return VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            operationName,
            () => this._mapper.MapFromStorageToDataModel(row, new() { IncludeVectors = includeVectors }));
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var operationName = "GetBatch";

        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;

        await foreach (var row in this._client.GetBatchAsync(this.CollectionName, keys, this._propertyReader.RecordDefinition, includeVectors, cancellationToken).ConfigureAwait(false))
        {
            yield return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                operationName,
                () => this._mapper.MapFromStorageToDataModel(row, new() { IncludeVectors = includeVectors }));
        }
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(TKey key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        await this._client.DeleteAsync(this.CollectionName, this._propertyReader.KeyPropertyStoragePropertyName, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this._client.DeleteBatchAsync(this.CollectionName, this._propertyReader.KeyPropertyStoragePropertyName, keys, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> VectorizableTextSearchAsync(string searchText, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
