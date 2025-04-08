// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using DistanceFunction = Microsoft.Azure.Cosmos.DistanceFunction;
using IndexKind = Microsoft.Extensions.VectorData.IndexKind;
using SKDistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure CosmosDB NoSQL as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord> :
    IVectorStoreRecordCollection<string, TRecord>,
    IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>,
    IKeywordHybridSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    private readonly Database _database;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    // TODO: Refactor this into the model (Co)
    /// <summary>The property to use as partition key.</summary>
    private readonly VectorStoreRecordPropertyModel _partitionKeyProperty;

    /// <summary>The mapper to use when mapping between the consumer data model and the Azure CosmosDB NoSQL record.</summary>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private readonly IVectorStoreRecordMapper<TRecord, JsonObject> _mapper;
#pragma warning restore CS0618

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="database"><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public AzureCosmosDBNoSQLVectorStoreRecordCollection(
        Database database,
        string collectionName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(collectionName);

        if (database.Client?.ClientOptions?.UseSystemTextJsonSerializerWithOptions is null)
        {
            throw new ArgumentException(
                $"Property {nameof(CosmosClientOptions.UseSystemTextJsonSerializerWithOptions)} in CosmosClient.ClientOptions " +
                $"is required to be configured for {nameof(AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>)}.");
        }

        // Assign.
        this._database = database;
        this.CollectionName = collectionName;
        this._options = options ?? new();
        var jsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default;
        this._model = new AzureCosmosDBNoSqlVectorStoreModelBuilder()
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, jsonSerializerOptions);

        // Assign mapper.
        this._mapper = this.InitializeMapper(jsonSerializerOptions);

        // Setup partition key property
        if (this._options.PartitionKeyPropertyName is not null)
        {
            if (!this._model.PropertyMap.TryGetValue(this._options.PartitionKeyPropertyName, out var property))
            {
                throw new ArgumentException($"Partition key property '{this._options.PartitionKeyPropertyName}' is not part of the record definition.");
            }

            if (property.Type != typeof(string))
            {
                throw new ArgumentException("Partition key property must be string.");
            }

            this._partitionKeyProperty = property;
        }
        else
        {
            // If partition key is not provided, use key property as a partition key.
            this._partitionKeyProperty = this._model.KeyProperty;
        }

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = AzureCosmosDBNoSQLConstants.VectorStoreSystemName,
            VectorStoreName = database.Id,
            CollectionName = collectionName
        };
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("GetContainerQueryIterator", async () =>
        {
            const string Query = "SELECT VALUE(c.id) FROM c WHERE c.id = @collectionName";

            var queryDefinition = new QueryDefinition(Query).WithParameter("@collectionName", this.CollectionName);

            using var feedIterator = this._database.GetContainerQueryIterator<string>(queryDefinition);

            while (feedIterator.HasMoreResults)
            {
                var next = await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

                foreach (var containerName in next.Resource)
                {
                    return true;
                }
            }

            return false;
        });
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("CreateContainer", () =>
            this._database.CreateContainerAsync(this.GetContainerProperties(), cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("DeleteContainer", () =>
            this._database
                .GetContainer(this.CollectionName)
                .DeleteContainerAsync(cancellationToken: cancellationToken));
    }

    #region Implementation of IVectorStoreRecordCollection<string, TRecord>

    /// <inheritdoc />
    public Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        // Use record key as partition key
        var compositeKey = new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key);

        return this.InternalDeleteAsync([compositeKey], cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        // Use record keys as partition keys
        var compositeKeys = keys.Select(key => new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key));

        return this.InternalDeleteAsync(compositeKeys, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        // Use record key as partition key
        var compositeKey = new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key);

        return await this.InternalGetAsync([compositeKey], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<string> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Use record keys as partition keys
        var compositeKeys = keys.Select(key => new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key));

        await foreach (var record in this.InternalGetAsync(compositeKeys, options, cancellationToken).ConfigureAwait(false))
        {
            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        var key = await this.InternalUpsertAsync(record, cancellationToken).ConfigureAwait(false);

        return key.RecordKey;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.InternalUpsertAsync(record, cancellationToken));

        var keys = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var key in keys)
        {
            if (key is not null)
            {
                yield return key.RecordKey;
            }
        }
    }

    #endregion

    #region Implementation of IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(AzureCosmosDBNoSQLCompositeKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return await this.InternalGetAsync([key], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var record in this.InternalGetAsync(keys, options, cancellationToken).ConfigureAwait(false))
        {
            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(AzureCosmosDBNoSQLCompositeKey key, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteAsync([key], cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteAsync(keys, cancellationToken);
    }

    /// <inheritdoc />
    Task<AzureCosmosDBNoSQLCompositeKey> IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>.UpsertAsync(TRecord record, CancellationToken cancellationToken)
    {
        return this.InternalUpsertAsync(record, cancellationToken);
    }

    /// <inheritdoc />
    async IAsyncEnumerable<AzureCosmosDBNoSQLCompositeKey> IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>.UpsertAsync(
        IEnumerable<TRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.InternalUpsertAsync(record, cancellationToken));

        var keys = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var key in keys)
        {
            if (key is not null)
            {
                yield return key;
            }
        }
    }

    /// <inheritdoc />
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
    {
        const string OperationName = "VectorizedSearch";
        const string ScorePropertyName = "SimilarityScore";

        this.VerifyVectorType(vector);
        Verify.NotLessThan(top, 1);

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(searchOptions);

#pragma warning disable CS0618 // Type or member is obsolete
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery(
            vector,
            null,
            this._model,
            vectorProperty.StorageName,
            null,
            ScorePropertyName,
            searchOptions.OldFilter,
            searchOptions.Filter,
            top,
            searchOptions.Skip,
            searchOptions.IncludeVectors);
#pragma warning restore CS0618 // Type or member is obsolete

        var searchResults = this.GetItemsAsync<JsonObject>(queryDefinition, cancellationToken);
        var mappedResults = this.MapSearchResultsAsync(
            searchResults,
            ScorePropertyName,
            OperationName,
            searchOptions.IncludeVectors,
            cancellationToken);
        return Task.FromResult(new VectorSearchResults<TRecord>(mappedResults));
    }

    /// <inheritdoc />
    public Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "VectorizedSearch";
        const string ScorePropertyName = "SimilarityScore";

        this.VerifyVectorType(vector);
        Verify.NotLessThan(top, 1);

        var searchOptions = options ?? s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = searchOptions.VectorProperty });
        var textProperty = this._model.GetFullTextDataPropertyOrSingle(searchOptions.AdditionalProperty);

#pragma warning disable CS0618 // Type or member is obsolete
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<TVector, TRecord>(
            vector,
            keywords,
            this._model,
            vectorProperty.StorageName,
            textProperty.StorageName,
            ScorePropertyName,
            searchOptions.OldFilter,
            searchOptions.Filter,
            top,
            searchOptions.Skip,
            searchOptions.IncludeVectors);
#pragma warning restore CS0618 // Type or member is obsolete

        var searchResults = this.GetItemsAsync<JsonObject>(queryDefinition, cancellationToken);
        var mappedResults = this.MapSearchResultsAsync(
            searchResults,
            ScorePropertyName,
            OperationName,
            searchOptions.IncludeVectors,
            cancellationToken);
        return Task.FromResult(new VectorSearchResults<TRecord>(mappedResults));
    }

    #endregion

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(Database) ? this._database :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    #region private

    private void VerifyVectorType<TVector>(TVector? vector)
    {
        Verify.NotNull(vector);

        var vectorType = vector.GetType();

        if (!AzureCosmosDBNoSqlVectorStoreModelBuilder.s_supportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the Azure CosmosDB NoSQL connector. " +
                $"Supported types are: {string.Join(", ", AzureCosmosDBNoSqlVectorStoreModelBuilder.s_supportedVectorTypes.Select(l => l.FullName))}");
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
                VectorStoreSystemName = AzureCosmosDBNoSQLConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

    /// <summary>
    /// Returns instance of <see cref="ContainerProperties"/> with applied indexing policy.
    /// More information here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-manage-indexing-policy"/>.
    /// </summary>
    private ContainerProperties GetContainerProperties()
    {
        // Process Vector properties.
        var embeddings = new Collection<Embedding>();
        var vectorIndexPaths = new Collection<VectorIndexPath>();

        var indexingPolicy = new IndexingPolicy
        {
            IndexingMode = this._options.IndexingMode,
            Automatic = this._options.Automatic
        };

        if (this._options.IndexingMode == IndexingMode.None)
        {
            return new ContainerProperties(this.CollectionName, partitionKeyPath: $"/{this._partitionKeyProperty.StorageName}")
            {
                IndexingPolicy = indexingPolicy
            };
        }

        foreach (var property in this._model.VectorProperties)
        {
            if (property.Dimensions is not > 0)
            {
                throw new VectorStoreOperationException($"Property {nameof(property.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{property.ModelName}' must be set to a positive integer to create a collection.");
            }

            var path = $"/{property.StorageName}";

            var embedding = new Embedding
            {
                DataType = GetDataType(property.Type, property.StorageName),
                Dimensions = (int)property.Dimensions,
                DistanceFunction = GetDistanceFunction(property.DistanceFunction, property.StorageName),
                Path = path
            };

            var vectorIndexPath = new VectorIndexPath
            {
                Type = GetIndexKind(property.IndexKind, property.StorageName),
                Path = path
            };

            embeddings.Add(embedding);
            vectorIndexPaths.Add(vectorIndexPath);
        }

        indexingPolicy.VectorIndexes = vectorIndexPaths;

        var fullTextPolicy = new FullTextPolicy() { FullTextPaths = new Collection<FullTextPath>() };
        var vectorEmbeddingPolicy = new VectorEmbeddingPolicy(embeddings);

        // Process Data properties.
        foreach (var property in this._model.DataProperties)
        {
            if (property.IsFilterable || property.IsFullTextSearchable)
            {
                indexingPolicy.IncludedPaths.Add(new IncludedPath { Path = $"/{property.StorageName}/?" });
            }
            if (property.IsFullTextSearchable)
            {
                indexingPolicy.FullTextIndexes.Add(new FullTextIndexPath { Path = $"/{property.StorageName}" });
                // TODO: Switch to using language from a setting.
                fullTextPolicy.FullTextPaths.Add(new FullTextPath { Path = $"/{property.StorageName}", Language = "en-US" });
            }
        }

        // Adding special mandatory indexing path.
        indexingPolicy.IncludedPaths.Add(new IncludedPath { Path = "/" });

        // Exclude vector paths to ensure optimized performance.
        foreach (var vectorIndexPath in vectorIndexPaths)
        {
            indexingPolicy.ExcludedPaths.Add(new ExcludedPath { Path = $"{vectorIndexPath.Path}/*" });
        }

        return new ContainerProperties(this.CollectionName, partitionKeyPath: $"/{this._partitionKeyProperty.StorageName}")
        {
            VectorEmbeddingPolicy = vectorEmbeddingPolicy,
            IndexingPolicy = indexingPolicy,
            FullTextPolicy = fullTextPolicy
        };
    }

    /// <summary>
    /// More information about Azure CosmosDB NoSQL index kinds here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#vector-indexing-policies" />.
    /// </summary>
    private static VectorIndexType GetIndexKind(string? indexKind, string vectorPropertyName)
        => indexKind switch
        {
            IndexKind.DiskAnn or null => VectorIndexType.DiskANN,
            IndexKind.Flat => VectorIndexType.Flat,
            IndexKind.QuantizedFlat => VectorIndexType.QuantizedFlat,
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };

    /// <summary>
    /// More information about Azure CosmosDB NoSQL distance functions here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#container-vector-policies" />.
    /// </summary>
    private static DistanceFunction GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
    {
        if (string.IsNullOrWhiteSpace(distanceFunction))
        {
            // Use default distance function.
            return DistanceFunction.Cosine;
        }

        return distanceFunction switch
        {
            SKDistanceFunction.CosineSimilarity => DistanceFunction.Cosine,
            SKDistanceFunction.DotProductSimilarity => DistanceFunction.DotProduct,
            SKDistanceFunction.EuclideanDistance => DistanceFunction.Euclidean,
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };
    }

    /// <summary>
    /// Returns <see cref="VectorDataType"/> based on vector property type.
    /// </summary>
    private static VectorDataType GetDataType(Type vectorDataType, string vectorPropertyName)
        => vectorDataType switch
        {
            Type type when type == typeof(ReadOnlyMemory<float>) || type == typeof(ReadOnlyMemory<float>?) => VectorDataType.Float32,
            Type type when type == typeof(ReadOnlyMemory<byte>) || type == typeof(ReadOnlyMemory<byte>?) => VectorDataType.Uint8,
            Type type when type == typeof(ReadOnlyMemory<sbyte>) || type == typeof(ReadOnlyMemory<sbyte>?) => VectorDataType.Int8,
            _ => throw new InvalidOperationException($"Data type '{vectorDataType}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };

    private async IAsyncEnumerable<TRecord> InternalGetAsync(
        IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "GetItemQueryIterator";

        var includeVectors = options?.IncludeVectors ?? false;

        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSelectQuery(
            this._model,
            this._model.KeyProperty.StorageName,
            this._partitionKeyProperty.StorageName,
            keys.ToList(),
            includeVectors);

        await foreach (var jsonObject in this.GetItemsAsync<JsonObject>(queryDefinition, cancellationToken).ConfigureAwait(false))
        {
            yield return VectorStoreErrorHandler.RunModelConversion(
                AzureCosmosDBNoSQLConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(jsonObject, new() { IncludeVectors = includeVectors }));
        }
    }

    private async Task<AzureCosmosDBNoSQLCompositeKey> InternalUpsertAsync(
        TRecord record,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(record);

        const string OperationName = "UpsertItem";

        var jsonObject = VectorStoreErrorHandler.RunModelConversion(
                AzureCosmosDBNoSQLConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record));

        var keyValue = jsonObject.TryGetPropertyValue(this._model.KeyProperty.StorageName!, out var jsonKey) ? jsonKey?.ToString() : null;
        var partitionKeyValue = jsonObject.TryGetPropertyValue(this._partitionKeyProperty.StorageName, out var jsonPartitionKey) ? jsonPartitionKey?.ToString() : null;

        if (string.IsNullOrWhiteSpace(keyValue))
        {
            throw new VectorStoreOperationException($"Key property {this._model.KeyProperty.ModelName} is not initialized.");
        }

        if (string.IsNullOrWhiteSpace(partitionKeyValue))
        {
            throw new VectorStoreOperationException($"Partition key property {this._partitionKeyProperty.ModelName} is not initialized.");
        }

        await this.RunOperationAsync(OperationName, () =>
            this._database
                .GetContainer(this.CollectionName)
                .UpsertItemAsync(jsonObject, new PartitionKey(partitionKeyValue), cancellationToken: cancellationToken))
            .ConfigureAwait(false);

        return new AzureCosmosDBNoSQLCompositeKey(keyValue!, partitionKeyValue!);
    }

    private async Task InternalDeleteAsync(IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys, CancellationToken cancellationToken)
    {
        Verify.NotNull(keys);

        var tasks = keys.Select(key =>
        {
            Verify.NotNullOrWhiteSpace(key.RecordKey);
            Verify.NotNullOrWhiteSpace(key.PartitionKey);

            return this.RunOperationAsync("DeleteItem", () =>
                this._database
                    .GetContainer(this.CollectionName)
                    .DeleteItemAsync<JsonObject>(key.RecordKey, new PartitionKey(key.PartitionKey), cancellationToken: cancellationToken));
        });

        await Task.WhenAll(tasks).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<T> GetItemsAsync<T>(QueryDefinition queryDefinition, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var iterator = this._database
            .GetContainer(this.CollectionName)
            .GetItemQueryIterator<T>(queryDefinition);

        while (iterator.HasMoreResults)
        {
            var response = await iterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

            foreach (var record in response.Resource)
            {
                if (record is not null)
                {
                    yield return record;
                }
            }
        }
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> MapSearchResultsAsync(
        IAsyncEnumerable<JsonObject> jsonObjects,
        string scorePropertyName,
        string operationName,
        bool includeVectors,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var jsonObject in jsonObjects.ConfigureAwait(false))
        {
            var score = jsonObject[scorePropertyName]?.AsValue().GetValue<double>();

            // Remove score from result object for mapping.
            jsonObject.Remove(scorePropertyName);

            var record = VectorStoreErrorHandler.RunModelConversion(
                AzureCosmosDBNoSQLConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.CollectionName,
                operationName,
                () => this._mapper.MapFromStorageToDataModel(jsonObject, new() { IncludeVectors = includeVectors }));

            yield return new VectorSearchResult<TRecord>(record, score);
        }
    }

#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private IVectorStoreRecordMapper<TRecord, JsonObject> InitializeMapper(JsonSerializerOptions jsonSerializerOptions)
    {
        if (this._options.JsonObjectCustomMapper is not null)
        {
            return this._options.JsonObjectCustomMapper;
        }

        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>))
        {
            var mapper = new AzureCosmosDBNoSQLGenericDataModelMapper(this._model, jsonSerializerOptions);
            return (mapper as IVectorStoreRecordMapper<TRecord, JsonObject>)!;
        }

        return new AzureCosmosDBNoSQLVectorStoreRecordMapper<TRecord>(this._model.KeyProperty, this._options.JsonSerializerOptions);
    }
#pragma warning restore CS0618

    #endregion
}
