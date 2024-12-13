﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;

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

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="dataSource">The data source to use for connecting to the database.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresVectorStoreRecordCollection(NpgsqlDataSource dataSource, string collectionName, PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default)
        : this(new PostgresVectorStoreDbClient(dataSource), collectionName, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="client">The client to use for interacting with the database.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <remarks>
    /// This constructor is internal. It allows internal code to create an instance of this class with a custom client.
    /// </remarks>
    internal PostgresVectorStoreRecordCollection(IPostgresVectorStoreDbClient client, string collectionName, PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default)
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
        this._propertyReader.VerifyDataProperties(PostgresConstants.SupportedDataTypes, PostgresConstants.SupportedEnumerableDataElementTypes);
        this._propertyReader.VerifyVectorProperties(PostgresConstants.SupportedVectorTypes);

        // Resolve mapper.
        // First, if someone has provided a custom mapper, use that.
        // If they didn't provide a custom mapper, and the record type is the generic data model, use the built in mapper for that.
        // Otherwise, use our own default mapper implementation for all other data models.
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
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DoesTableExists";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DoesTableExistsAsync(this.CollectionName, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollection";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(false, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollectionIfNotExists";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(true, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteCollection";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteTableAsync(this.CollectionName, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task<TKey> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Upsert";

        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            PostgresConstants.DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        Verify.NotNull(storageModel);

        var keyObj = storageModel[this._propertyReader.KeyPropertyStoragePropertyName];
        Verify.NotNull(keyObj);
        TKey key = (TKey)keyObj!;

        return this.RunOperationAsync(OperationName, async () =>
            {
                await this._client.UpsertAsync(this.CollectionName, storageModel, this._propertyReader.KeyPropertyStoragePropertyName, cancellationToken).ConfigureAwait(false);
                return key;
            }
        );
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertBatch";

        var storageModels = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
            PostgresConstants.DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record))).ToList();

        var keys = storageModels.Select(model => model[this._propertyReader.KeyPropertyStoragePropertyName]!).ToList();

        await this.RunOperationAsync(OperationName, () =>
            this._client.UpsertBatchAsync(this.CollectionName, storageModels, this._propertyReader.KeyPropertyStoragePropertyName, cancellationToken)
        ).ConfigureAwait(false);

        foreach (var key in keys) { yield return (TKey)key!; }
    }

    /// <inheritdoc/>
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Get";

        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;

        return this.RunOperationAsync<TRecord?>(OperationName, async () =>
        {
            var row = await this._client.GetAsync(this.CollectionName, key, this._propertyReader.RecordDefinition.Properties, includeVectors, cancellationToken).ConfigureAwait(false);

            if (row is null) { return default; }
            return VectorStoreErrorHandler.RunModelConversion(
                PostgresConstants.DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(row, new() { IncludeVectors = includeVectors }));
        });
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetBatch";

        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;

        return PostgresVectorStoreUtils.WrapAsyncEnumerableAsync(
            this._client.GetBatchAsync(this.CollectionName, keys, this._propertyReader.RecordDefinition.Properties, includeVectors, cancellationToken)
                .SelectAsync(row =>
                    VectorStoreErrorHandler.RunModelConversion(
                        PostgresConstants.DatabaseName,
                        this.CollectionName,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(row, new() { IncludeVectors = includeVectors })),
                    cancellationToken
                ),
            OperationName,
            this.CollectionName
        );
    }

    /// <inheritdoc/>
    public Task DeleteAsync(TKey key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Delete";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteAsync(this.CollectionName, this._propertyReader.KeyPropertyStoragePropertyName, key, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteBatch";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteBatchAsync(this.CollectionName, this._propertyReader.KeyPropertyStoragePropertyName, keys, cancellationToken)
        );
    }

    /// <inheritdoc />
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "VectorizedSearch";

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

        return this.RunOperationAsync(OperationName, () =>
        {
            var results = this._client.GetNearestMatchesAsync(
                this.CollectionName,
                this._propertyReader.RecordDefinition.Properties,
                vectorProperty,
                pgVector,
                searchOptions.Top,
                searchOptions.Filter,
                searchOptions.Skip,
                searchOptions.IncludeVectors,
                cancellationToken)
            .SelectAsync(result =>
                {
                    var record = VectorStoreErrorHandler.RunModelConversion(
                        PostgresConstants.DatabaseName,
                        this.CollectionName,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(
                            result.Row, new StorageToDataModelMapperOptions() { IncludeVectors = searchOptions.IncludeVectors })
                    );

                    return new VectorSearchResult<TRecord>(record, result.Distance);
                }, cancellationToken);

            return Task.FromResult(new VectorSearchResults<TRecord>(results));
        });
    }

    private Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken = default)
    {
        return this._client.CreateTableAsync(this.CollectionName, this._propertyReader.RecordDefinition.Properties, ifNotExists, cancellationToken);
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
                VectorStoreType = PostgresConstants.DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
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
                VectorStoreType = PostgresConstants.DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }
}
