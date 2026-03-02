// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Net;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using DistanceFunction = Microsoft.Azure.Cosmos.DistanceFunction;
using IndexKind = Microsoft.Extensions.VectorData.IndexKind;
using MEAI = Microsoft.Extensions.AI;
using SKDistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure CosmosDB NoSQL as the underlying storage.
/// </summary>
/// <typeparam name="TKey">
///     The data type of the record key. Supported types are <see cref="string"/> and <see cref="Guid"/> (in which case the partition key
///     is the document ID), and <see cref="CosmosNoSqlKey"/> (for other partition key configurations).</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class CosmosNoSqlCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>, IKeywordHybridSearchable<TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    private readonly ClientWrapper _clientWrapper;

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    private readonly Database _database;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    // TODO: Refactor this into the model
    /// <summary>The properties to use as partition key (supports hierarchical partition keys up to 3 levels).</summary>
    private readonly List<PropertyModel> _partitionKeyProperties;

    /// <summary>The mapper to use when mapping between the consumer data model and the Azure CosmosDB NoSQL record.</summary>
    private readonly ICosmosNoSqlMapper<TRecord> _mapper;

    /// <inheritdoc />
    public override string Name { get; }

    /// <summary>The indexing mode in the Azure Cosmos DB service.</summary>
    private readonly IndexingMode _indexingMode;

    /// <summary>Whether automatic indexing is enabled for a collection in the Azure Cosmos DB service.</summary>
    private readonly bool _automatic;

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="database"><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</param>
    /// <param name="name">The name of the collection that this <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public CosmosNoSqlCollection(Database database, string name, CosmosNoSqlCollectionOptions? options = default)
        : this(new(database.Client, ownsClient: false), _ => database, name, options)
    {
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(name);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="name">The name of the collection that this <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="clientOptions">Optional configuration options for <see cref="CosmosClient"/>.</param>
    /// <param name="options">Optional configuration options for <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public CosmosNoSqlCollection(
        string connectionString,
        string databaseName,
        string name,
        CosmosClientOptions? clientOptions = null,
        CosmosNoSqlCollectionOptions? options = null)
        : this(
            new ClientWrapper(new CosmosClient(connectionString, clientOptions), ownsClient: true),
            client => client.GetDatabase(databaseName),
            name,
            options)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);
        Verify.NotNullOrWhiteSpace(name);
    }

    internal CosmosNoSqlCollection(
        ClientWrapper clientWrapper,
        Func<CosmosClient, Database> databaseProvider,
        string name,
        CosmosNoSqlCollectionOptions? options)
        : this(
            clientWrapper,
            databaseProvider,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(CosmosNoSqlDynamicCollection)))
                : new CosmosNoSqlModelBuilder()
                    .Build(typeof(TRecord), typeof(TKey), options.Definition, options.EmbeddingGenerator, options.JsonSerializerOptions ?? JsonSerializerOptions.Default),
            options)
    {
    }

    internal CosmosNoSqlCollection(
        ClientWrapper clientWrapper,
        Func<CosmosClient, Database> databaseProvider,
        string name,
        Func<CosmosNoSqlCollectionOptions, CollectionModel> modelFactory,
        CosmosNoSqlCollectionOptions? options)
    {
        // Validate TKey: must be string or Guid (partition key = document ID), CosmosNoSqlKey (other parittion key cases), or object (used by CosmosNoSqlDynamicCollection).
        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(Guid) && typeof(TKey) != typeof(CosmosNoSqlKey) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException($"The key type must be string, Guid, or CosmosNoSqlKey. Received: {typeof(TKey).Name}");
        }

        try
        {
            this._database = databaseProvider(clientWrapper.Client);

            if (clientWrapper.Client.ClientOptions?.UseSystemTextJsonSerializerWithOptions is null)
            {
                throw new ArgumentException(
                    $"Property {nameof(CosmosClientOptions.UseSystemTextJsonSerializerWithOptions)} in CosmosClient.ClientOptions " +
                    $"is required to be configured for {this.GetType().Name}.");
            }

            options ??= CosmosNoSqlCollectionOptions.Default;

            // Assign.
            this.Name = name;
            this._model = modelFactory(options);
            this._indexingMode = options.IndexingMode;
            this._automatic = options.Automatic;
            var jsonSerializerOptions = options.JsonSerializerOptions ?? JsonSerializerOptions.Default;

            // Assign mapper.
            this._mapper = typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? (new CosmosNoSqlDynamicMapper(this._model, jsonSerializerOptions) as ICosmosNoSqlMapper<TRecord>)!
                : new CosmosNoSqlMapper<TRecord>(this._model, options.JsonSerializerOptions);

            // Setup partition key properties (supports hierarchical partition keys up to 3 levels)
            if (options.PartitionKeyProperties is null)
            {
                // No partition key property names configured: default to using the key property as the partition key.
                // This is the most common Cosmos DB strategy where the document ID and partition key are the same value.
                this._partitionKeyProperties = [this._model.KeyProperty];
            }
            else
            {
                if (options.PartitionKeyProperties.Count > 3)
                {
                    throw new ArgumentException("Cosmos DB supports at most 3 levels of hierarchical partition keys.");
                }

                this._partitionKeyProperties = new List<PropertyModel>(options.PartitionKeyProperties.Count);

                foreach (var propertyName in options.PartitionKeyProperties)
                {
                    if (!this._model.PropertyMap.TryGetValue(propertyName, out var property))
                    {
                        throw new ArgumentException($"Partition key property '{propertyName}' is not part of the record definition.");
                    }

                    if (property.Type != typeof(string) && property.Type != typeof(bool) && property.Type != typeof(double) && property.Type != typeof(Guid))
                    {
                        throw new ArgumentException($"Partition key property '{propertyName}' must be string, bool, double, or Guid.");
                    }

                    this._partitionKeyProperties.Add(property);
                }
            }

            // When using simple key types (string/Guid), the partition key must be the key property only,
            // since the partition key value cannot be independently specified via a simple key.
            // Users who need hierarchical partition keys, a non-key partition key, or no partition key at all
            // must use CosmosNoSqlKey as the key type.
            if ((typeof(TKey) == typeof(string) || typeof(TKey) == typeof(Guid))
                && (this._partitionKeyProperties is not [var singlePkProperty] || singlePkProperty != this._model.KeyProperty))
            {
                throw new ArgumentException(
                    $"When using {typeof(TKey).Name} as the key type, the partition key must be the key property " +
                    $"('{this._model.KeyProperty.ModelName}'). To use a different partition key configuration, use CosmosNoSqlKey as the key type.");
            }

            this._collectionMetadata = new()
            {
                VectorStoreSystemName = CosmosNoSqlConstants.VectorStoreSystemName,
                VectorStoreName = this._database.Id,
                CollectionName = name
            };
        }
        catch (Exception)
        {
            // Something went wrong, we dispose the client and don't store a reference.
            clientWrapper.Dispose();

            throw;
        }

        this._clientWrapper = clientWrapper;
    }

    /// <inheritdoc/>
    protected override void Dispose(bool disposing)
    {
        this._clientWrapper.Dispose();
        base.Dispose(disposing);
    }

    /// <inheritdoc />
    public override async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "ListCollectionNamesAsync";
        const string Query = "SELECT VALUE(c.id) FROM c WHERE c.id = @collectionName";
        var queryDefinition = new QueryDefinition(Query).WithParameter("@collectionName", this.Name);

        using var feedIterator = VectorStoreErrorHandler.RunOperation<FeedIterator<string>, CosmosException>(
            this._collectionMetadata,
            OperationName,
            () => this._database.GetContainerQueryIterator<string>(queryDefinition));

        using var errorHandlingFeedIterator = new ErrorHandlingFeedIterator<string>(feedIterator, this._collectionMetadata, OperationName);

        while (errorHandlingFeedIterator.HasMoreResults)
        {
            var next = await errorHandlingFeedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

            foreach (var containerName in next.Resource)
            {
                return true;
            }
        }

        return false;
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        // Don't even try to create if the collection already exists.
        if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            return;
        }

        try
        {
            await this._database.CreateContainerAsync(this.GetContainerProperties(), cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.Conflict)
        {
            // Do nothing, since the container is already created.
        }
        catch (CosmosException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = CosmosNoSqlConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "CreateContainer"
            };
        }
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this._database
                .GetContainer(this.Name)
                .DeleteContainerAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Do nothing, since the container is already deleted.
        }
        catch (CosmosException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = CosmosNoSqlConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "DeleteContainer"
            };
        }
    }

    /// <inheritdoc />
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var (documentId, partitionKey) = this.GetDocumentIdAndPartitionKey(key);

        return this.RunOperationAsync("DeleteItem", async () =>
        {
            try
            {
                await this._database
                    .GetContainer(this.Name)
                    .DeleteItemAsync<JsonObject>(documentId, partitionKey, cancellationToken: cancellationToken)
                    .ConfigureAwait(false);
                return 0;
            }
            catch (CosmosException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                // Ignore not found errors
                return 0;
            }
        });
    }

    // TODO: Implement bulk delete, #11350

    /// <inheritdoc />
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        const string OperationName = "ReadItem";

        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var (documentId, partitionKey) = this.GetDocumentIdAndPartitionKey(key);

        var jsonObject = await this.RunOperationAsync(OperationName, async () =>
        {
            try
            {
                var response = await this._database
                    .GetContainer(this.Name)
                    .ReadItemAsync<JsonObject>(documentId, partitionKey, cancellationToken: cancellationToken)
                    .ConfigureAwait(false);
                return response.Resource;
            }
            catch (CosmosException e) when (e.StatusCode == HttpStatusCode.NotFound)
            {
                return null;
            }
        }).ConfigureAwait(false);

        return jsonObject is null ? default : this._mapper.MapFromStorageToDataModel(jsonObject, includeVectors);
    }

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        RecordRetrievalOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "ReadManyItems";

        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var items = keys.Select(this.GetDocumentIdAndPartitionKey).ToList();

        if (items.Count == 0)
        {
            yield break;
        }

        var response = await this.RunOperationAsync(OperationName, () =>
            this._database
                .GetContainer(this.Name)
                .ReadManyItemsAsync<JsonObject>(items, cancellationToken: cancellationToken))
            .ConfigureAwait(false);

        foreach (var jsonObject in response.Resource)
        {
            var record = this._mapper.MapFromStorageToDataModel(jsonObject, includeVectors);

            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        (_, var generatedEmbeddings) = await ProcessEmbeddingsAsync(this._model, [record], cancellationToken).ConfigureAwait(false);

        await this.UpsertCoreAsync(record, recordIndex: 0, generatedEmbeddings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        (records, var generatedEmbeddings) = await ProcessEmbeddingsAsync(this._model, records, cancellationToken).ConfigureAwait(false);

        // TODO: Do proper bulk upsert rather than single inserts, #11350
        var i = 0;

        foreach (var record in records)
        {
            await this.UpsertCoreAsync(record, i++, generatedEmbeddings, cancellationToken).ConfigureAwait(false);
        }
    }

    private async Task UpsertCoreAsync(TRecord record, int recordIndex, IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings, CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertItem";

        // Handle auto-generated keys (client-side for Cosmos DB NoSQL, which doesn't support server-side auto-generation)
        var keyProperty = this._model.KeyProperty;
        if (keyProperty.IsAutoGenerated && keyProperty.GetValue<Guid>(record) == Guid.Empty)
        {
            keyProperty.SetValue(record, Guid.NewGuid());
        }

        var partitionKey = this.BuildPartitionKey(record);

        var jsonObject = this._mapper.MapFromDataToStorageModel(record, recordIndex, generatedEmbeddings);

        var keyValue = jsonObject.TryGetPropertyValue(this._model.KeyProperty.StorageName!, out var jsonKey) ? jsonKey?.ToString() : null;

        if (string.IsNullOrWhiteSpace(keyValue))
        {
            throw new ArgumentException($"Key property {this._model.KeyProperty.ModelName} is not initialized.");
        }

        await this.RunOperationAsync(OperationName, () =>
            this._database
                .GetContainer(this.Name)
                .UpsertItemAsync(jsonObject, partitionKey, cancellationToken: cancellationToken))
            .ConfigureAwait(false);
    }

    private static async ValueTask<(IEnumerable<TRecord> records, IReadOnlyList<MEAI.Embedding>?[]?)> ProcessEmbeddingsAsync(
        CollectionModel model,
        IEnumerable<TRecord> records,
        CancellationToken cancellationToken)
    {
        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = model.VectorProperties[i];

            if (CosmosNoSqlModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return (records, null);
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<MEAI.Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await floatTask.ConfigureAwait(false);
            }
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<byte>>(records, cancellationToken, out var byteTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<MEAI.Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await byteTask.ConfigureAwait(false);
            }
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<sbyte>>(records, cancellationToken, out var sbyteTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<MEAI.Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await sbyteTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        return (records, generatedEmbeddings);
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        const string OperationName = "VectorizedSearch";
        const string ScorePropertyName = "SimilarityScore";

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
        object vector = await GetSearchVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

#pragma warning disable CS0618 // Type or member is obsolete
        var queryDefinition = CosmosNoSqlCollectionQueryBuilder.BuildSearchQuery(
            vector,
            null,
            this._model,
            vectorProperty.StorageName,
            vectorProperty.DistanceFunction,
            textPropertyName: null,
            ScorePropertyName,
            options.OldFilter,
            options.Filter,
            options.ScoreThreshold,
            top,
            options.Skip,
            options.IncludeVectors);
#pragma warning restore CS0618 // Type or member is obsolete

        var searchResults = this.GetItemsAsync<JsonObject>(queryDefinition, OperationName, cancellationToken);

        await foreach (var record in this.MapSearchResultsAsync(searchResults, ScorePropertyName, OperationName, options.IncludeVectors, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    private static async ValueTask<object> GetSearchVectorAsync<TInput>(TInput searchValue, VectorPropertyModel vectorProperty, CancellationToken cancellationToken)
        where TInput : notnull
        => searchValue switch
        {
            // float32
            ReadOnlyMemory<float> m => m,
            float[] a => new ReadOnlyMemory<float>(a),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            // int8
            ReadOnlyMemory<sbyte> m => m,
            sbyte[] a => new ReadOnlyMemory<sbyte>(a),
            Embedding<sbyte> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<sbyte>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            // uint8
            ReadOnlyMemory<byte> m => m,
            byte[] a => new ReadOnlyMemory<byte>(a),
            Embedding<byte> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<byte>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), CosmosNoSqlModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

    #endregion Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        const string OperationName = "GetAsync";

        options ??= new();

        var (whereClause, filterParameters) = new CosmosNoSqlFilterTranslator().Translate(filter, this._model);

        var queryDefinition = CosmosNoSqlCollectionQueryBuilder.BuildSearchQuery(
            this._model,
            whereClause,
            filterParameters,
            options,
            top);

        var searchResults = this.GetItemsAsync<JsonObject>(queryDefinition, OperationName, cancellationToken);

        await foreach (var jsonObject in searchResults.ConfigureAwait(false))
        {
            var record = this._mapper.MapFromStorageToDataModel(jsonObject, options.IncludeVectors);

            yield return record;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(
        TInput searchValue,
        ICollection<string> keywords,
        int top,
        HybridSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        const string OperationName = "VectorizedSearch";
        const string ScorePropertyName = "SimilarityScore";

        this.VerifyVectorType(searchValue);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        object vector = await GetSearchVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);
        var textProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

#pragma warning disable CS0618 // Type or member is obsolete
        var queryDefinition = CosmosNoSqlCollectionQueryBuilder.BuildSearchQuery<TRecord>(
            vector,
            keywords,
            this._model,
            vectorProperty.StorageName,
            vectorProperty.DistanceFunction,
            textProperty.StorageName,
            ScorePropertyName,
            options.OldFilter,
            options.Filter,
            options.ScoreThreshold,
            top,
            options.Skip,
            options.IncludeVectors);
#pragma warning restore CS0618 // Type or member is obsolete

        var searchResults = this.GetItemsAsync<JsonObject>(queryDefinition, OperationName, cancellationToken);

        await foreach (var record in this.MapSearchResultsAsync(searchResults, ScorePropertyName, OperationName, options.IncludeVectors, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(Database) ? this._database :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    #region private

    private void VerifyVectorType<TVector>(TVector? vector)
    {
        Verify.NotNull(vector);

        var vectorType = vector.GetType();

        if (!CosmosNoSqlModelBuilder.IsVectorPropertyTypeValidCore(vectorType, out var supportedTypes))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the Azure CosmosDB NoSQL connector. Supported types are: {supportedTypes}");
        }
    }

    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
        => VectorStoreErrorHandler.RunOperationAsync<T, CosmosException>(
            this._collectionMetadata,
            operationName,
            operation);

    /// <summary>
    /// Gets the document ID and partition key from a key.
    /// </summary>
    private (string DocumentId, PartitionKey PartitionKey) GetDocumentIdAndPartitionKey(TKey key)
        => key switch
        {
            CosmosNoSqlKey cosmosKey => (cosmosKey.DocumentId, cosmosKey.PartitionKey),
            string s => (s, new PartitionKey(s)),
            Guid g => (g.ToString(), new PartitionKey(g.ToString())),
            _ => throw new InvalidOperationException(
                $"Keys must be of type string, Guid, or CosmosNoSqlKey. Received key of type '{key.GetType().FullName}'.")
        };

    /// <summary>
    /// Returns instance of <see cref="ContainerProperties"/> with applied indexing policy.
    /// More information here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-manage-indexing-policy"/>.
    /// </summary>
    private ContainerProperties GetContainerProperties()
    {
        var indexingPolicy = new IndexingPolicy
        {
            IndexingMode = this._indexingMode,
            Automatic = this._automatic
        };

        var containerProperties = new ContainerProperties(
            this.Name,
            partitionKeyPaths: this._partitionKeyProperties.Count > 0
                ? this._partitionKeyProperties.Select(p => $"/{p.StorageName}").ToList()
                : ["/id"])
        {
            IndexingPolicy = indexingPolicy
        };

        if (this._indexingMode == IndexingMode.None)
        {
            return containerProperties;
        }

        // Process Vector properties.
        var embeddings = new Collection<Azure.Cosmos.Embedding>();
        var vectorIndexPaths = new Collection<VectorIndexPath>();

        foreach (var property in this._model.VectorProperties)
        {
            var path = $"/{property.StorageName}";

            var embedding = new Azure.Cosmos.Embedding
            {
                DataType = GetDataType(property.EmbeddingType, property.StorageName),
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

        var fullTextPolicy = new FullTextPolicy() { FullTextPaths = [] };
        var vectorEmbeddingPolicy = new VectorEmbeddingPolicy(embeddings);

        // Process Data properties.
        foreach (var property in this._model.DataProperties)
        {
            if (property.IsIndexed || property.IsFullTextIndexed)
            {
                indexingPolicy.IncludedPaths.Add(new IncludedPath { Path = $"/{property.StorageName}/?" });
            }
            if (property.IsFullTextIndexed)
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

        containerProperties.VectorEmbeddingPolicy = vectorEmbeddingPolicy;
        containerProperties.FullTextPolicy = fullTextPolicy;

        return containerProperties;
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
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };

    /// <summary>
    /// More information about Azure CosmosDB NoSQL distance functions here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#container-vector-policies" />.
    /// </summary>
    private static DistanceFunction GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
        => distanceFunction switch
        {
            SKDistanceFunction.CosineSimilarity or null => DistanceFunction.Cosine,
            SKDistanceFunction.DotProductSimilarity => DistanceFunction.DotProduct,
            SKDistanceFunction.EuclideanDistance => DistanceFunction.Euclidean,

            _ => throw new NotSupportedException($"Distance function '{distanceFunction}' for {nameof(VectorStoreVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };

    /// <summary>
    /// Returns <see cref="VectorDataType"/> based on vector property type.
    /// </summary>
    private static VectorDataType GetDataType(Type vectorDataType, string vectorPropertyName)
        => (Nullable.GetUnderlyingType(vectorDataType) ?? vectorDataType) switch
        {
            Type type when type == typeof(ReadOnlyMemory<float>) || type == typeof(Embedding<float>) || type == typeof(float[])
                => VectorDataType.Float32,

            Type type when type == typeof(ReadOnlyMemory<byte>) || type == typeof(Embedding<byte>) || type == typeof(byte[])
                => VectorDataType.Uint8,

            Type type when type == typeof(ReadOnlyMemory<sbyte>) || type == typeof(Embedding<sbyte>) || type == typeof(sbyte[])
                => VectorDataType.Int8,

            _ => throw new InvalidOperationException($"Data type '{vectorDataType}' for {nameof(VectorStoreVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };

    private async IAsyncEnumerable<T> GetItemsAsync<T>(QueryDefinition queryDefinition, string operationName, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var feedIterator = VectorStoreErrorHandler.RunOperation<FeedIterator<T>, CosmosException>(
            this._collectionMetadata,
            operationName,
            () => this._database
                .GetContainer(this.Name)
                .GetItemQueryIterator<T>(queryDefinition));
        using var errorHandlingFeedIterator = new ErrorHandlingFeedIterator<T>(feedIterator, this._collectionMetadata, operationName);

        while (errorHandlingFeedIterator.HasMoreResults)
        {
            var response = await errorHandlingFeedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

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

            var record = this._mapper.MapFromStorageToDataModel(jsonObject, includeVectors);

            yield return new VectorSearchResult<TRecord>(record, score);
        }
    }

    /// <summary>
    /// Builds a PartitionKey from the partition key property values in the record.
    /// Supports single and hierarchical partition keys.
    /// </summary>
    private PartitionKey BuildPartitionKey(TRecord record)
    {
        switch (this._partitionKeyProperties)
        {
            case []:
                return PartitionKey.None;

            // Single partition key
            case [var property]:
            {
                return property.Type switch
                {
                    Type t when t == typeof(string) => new PartitionKey(property.GetValue<string>(record)),
                    Type t when t == typeof(bool) => new PartitionKey(property.GetValue<bool>(record)),
                    Type t when t == typeof(double) => new PartitionKey(property.GetValue<double>(record)),
                    Type t when t == typeof(Guid) => new PartitionKey(property.GetValue<Guid>(record).ToString()),
                    _ => throw new InvalidOperationException($"Unsupported partition key type: {property.Type.Name}")
                };
            }

            // Hierarchical partition key (2 or 3 levels)
            default:
                var builder = new PartitionKeyBuilder();

                foreach (var property in this._partitionKeyProperties)
                {
                    _ = property.Type switch
                    {
                        Type t when t == typeof(string) => builder.Add(property.GetValue<string>(record)),
                        Type t when t == typeof(bool) => builder.Add(property.GetValue<bool>(record)),
                        Type t when t == typeof(double) => builder.Add(property.GetValue<double>(record)),
                        Type t when t == typeof(Guid) => builder.Add(property.GetValue<Guid>(record).ToString()),
                        _ => throw new InvalidOperationException($"Unsupported partition key type: {property.Type.Name}")
                    };
                }

                return builder.Build();
        }
    }

    #endregion
}
