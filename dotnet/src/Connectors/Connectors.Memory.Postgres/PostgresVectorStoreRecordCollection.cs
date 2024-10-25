// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Represents a collection of vector store records in a Postgres database.
/// </summary>
/// <typeparam name="TKey">The type of the key.</typeparam>
/// <typeparam name="TRecord">The type of the record.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PostgresVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
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

    /// <summary>The logger to use for logging.</summary>
    private readonly ILogger<PostgresVectorStoreRecordCollection<TKey, TRecord>> _logger;

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="client">The Postgres client used to interact with the database.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <param name="logger">The logger to use for logging.</param>
    public PostgresVectorStoreRecordCollection(IPostgresVectorStoreDbClient client, string collectionName, PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ILogger<PostgresVectorStoreRecordCollection<TKey, TRecord>>? logger = null)
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
        this._logger = logger ?? NullLogger<PostgresVectorStoreRecordCollection<TKey, TRecord>>.Instance;

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
        else if (typeof(TRecord).IsGenericType && typeof(TRecord).GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
        {
            this._mapper = (new PostgresGenericDataModelMapper<TKey>(this._propertyReader) as IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>)!;
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
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        await this.InternalCreateCollectionAsync(false, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.InternalCreateCollectionAsync(true, cancellationToken);
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

        await this._client.UpsertAsync(this.CollectionName, storageModel, this._propertyReader.KeyPropertyStoragePropertyName, cancellationToken).ConfigureAwait(false);
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

        var row = await this._client.GetAsync(this.CollectionName, key, this._propertyReader.RecordDefinition.Properties, includeVectors, cancellationToken).ConfigureAwait(false);

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

        await foreach (var row in this._client.GetBatchAsync(this.CollectionName, keys, this._propertyReader.RecordDefinition.Properties, includeVectors, cancellationToken).ConfigureAwait(false))
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

    /// <inheritdoc />
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        var vectorType = vector.GetType();

        if (!PostgresConstants.SupportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the SQLite connector. " +
                $"Supported types are: {string.Join(", ", PostgresConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this.GetVectorPropertyForSearch(searchOptions.VectorPropertyName);

        if (vectorProperty is null)
        {
            throw new InvalidOperationException("The collection does not have any vector properties, so vector search is not possible.");
        }

        var pgVector = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        Verify.NotNull(pgVector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = searchOptions.Top + searchOptions.Skip;

        var results = this._client.GetNearestMatchesAsync(
            this.CollectionName,
            this._propertyReader.RecordDefinition.Properties,
            vectorProperty,
            pgVector,
            searchOptions.Top,
            searchOptions.Filter,
            searchOptions.Skip,
            searchOptions.IncludeVectors,
            cancellationToken
            ).Select(result =>
            {
                var record = this._mapper.MapFromStorageToDataModel(
                    result.Row, new StorageToDataModelMapperOptions() { IncludeVectors = searchOptions.IncludeVectors });

                return new VectorSearchResult<TRecord>(record, result.Distance);
            }, cancellationToken);

        return Task.FromResult(new VectorSearchResults<TRecord>(results));
    }

    private async Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken = default)
    {
        await this._client.CreateTableAsync(this.CollectionName, this._propertyReader.RecordDefinition.Properties, ifNotExists, cancellationToken).ConfigureAwait(false);
        // Create indexes for vector properties.
        foreach (var vectorProperty in this._propertyReader.VectorProperties)
        {
            var indexKind = vectorProperty.IndexKind ?? PostgresConstants.DefaultIndexKind;

            // Ensure the dimensionality of the vector is supported for indexing.
            if (indexKind == IndexKind.Hnsw)
            {
                if (vectorProperty.Dimensions > 2000)
                {
                    throw new NotSupportedException(
                        $"The provided vector property {vectorProperty.DataModelPropertyName} has {vectorProperty.Dimensions} dimensions, which is not supported by the HNSW index. The maximum number of dimensions supported by the HNSW index is 2000. Index not created."
                    );
                }
            }
            await this._client.CreateVectorIndexAsync(this.CollectionName, vectorProperty, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Get vector property to use for a search by using the storage name for the field name from options
    /// if available, and falling back to the first vector property in <typeparamref name="TRecord"/> if not.
    /// </summary>
    /// <param name="vectorFieldName">The vector field name.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided field name is not a valid field name.</exception>
    private VectorStoreRecordVectorProperty? GetVectorPropertyForSearch(string? vectorFieldName)
    {
        // If vector property name is provided in options, try to find it in schema or throw an exception.
        if (!string.IsNullOrWhiteSpace(vectorFieldName))
        {
            // Check vector properties by data model property name.
            var vectorProperty = this._propertyReader.VectorProperties
                .FirstOrDefault(l => l.DataModelPropertyName.Equals(vectorFieldName, StringComparison.Ordinal));

            if (vectorProperty is not null)
            {
                return vectorProperty;
            }

            throw new InvalidOperationException($"The {typeof(TRecord).FullName} type does not have a vector property named '{vectorFieldName}'.");
        }

        // If vector property is not provided in options, return first vector property from schema.
        return this._propertyReader.VectorProperty;
    }
}
