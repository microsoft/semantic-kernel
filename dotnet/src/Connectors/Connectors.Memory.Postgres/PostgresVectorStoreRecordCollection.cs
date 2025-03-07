// Copyright (c) Microsoft. All rights reserved.

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
public class PostgresVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
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
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

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
    public virtual Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DoesTableExists";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DoesTableExistsAsync(this.CollectionName, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public virtual Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollection";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(false, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public virtual Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollectionIfNotExists";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(true, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public virtual Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteCollection";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteTableAsync(this.CollectionName, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public virtual Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
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
    public virtual async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        const string OperationName = "UpsertBatch";

        var storageModels = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
            PostgresConstants.DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record))).ToList();

        if (storageModels.Count == 0)
        {
            yield break;
        }

        var keys = storageModels.Select(model => model[this._propertyReader.KeyPropertyStoragePropertyName]!).ToList();

        await this.RunOperationAsync(OperationName, () =>
            this._client.UpsertBatchAsync(this.CollectionName, storageModels, this._propertyReader.KeyPropertyStoragePropertyName, cancellationToken)
        ).ConfigureAwait(false);

        foreach (var key in keys) { yield return (TKey)key!; }
    }

    /// <inheritdoc/>
    public virtual Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
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
    public virtual IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
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
    public virtual Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Delete";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteAsync(this.CollectionName, this._propertyReader.KeyPropertyStoragePropertyName, key, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public virtual Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "DeleteBatch";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteBatchAsync(this.CollectionName, this._propertyReader.KeyPropertyStoragePropertyName, keys, cancellationToken)
        );
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "VectorizedSearch";

        Verify.NotNull(vector);

        var vectorType = vector.GetType();

        if (!PostgresConstants.SupportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the PostgreSQL connector. " +
                $"Supported types are: {string.Join(", ", PostgresConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(searchOptions);

        var pgVector = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        Verify.NotNull(pgVector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = searchOptions.Top + searchOptions.Skip;

        return this.RunOperationAsync(OperationName, () =>
        {
            var results = this._client.GetNearestMatchesAsync(
                this.CollectionName,
                this._propertyReader,
                vectorProperty,
                pgVector,
                searchOptions.Top,
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
                searchOptions.OldFilter,
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
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

    private async Task RunOperationAsync(string operationName, Func<Task> operation)
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is not NotSupportedException)
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
        catch (Exception ex) when (ex is not NotSupportedException)
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
