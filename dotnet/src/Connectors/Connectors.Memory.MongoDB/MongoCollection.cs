// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using MongoDB.Bson;
using MongoDB.Driver;
using MEVD = Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Service for storing and retrieving vector records, that uses MongoDB as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Must be <see cref="string"/>.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class MongoCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>, IKeywordHybridSearchable<TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>Property name to be used for search similarity score value.</summary>
    private const string ScorePropertyName = "similarityScore";

    /// <summary>Property name to be used for search document value.</summary>
    private const string DocumentPropertyName = "document";

    /// <summary>The default options for vector search.</summary>
    private static readonly MEVD.VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</summary>
    private readonly IMongoDatabase _mongoDatabase;

    /// <summary>MongoDB collection to perform record operations.</summary>
    private readonly IMongoCollection<BsonDocument> _mongoCollection;

    /// <summary>Interface for mapping between a storage model, and the consumer record data model.</summary>
    private readonly IMongoMapper<TRecord> _mapper;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <inheritdoc />
    public override string Name { get; }

    /// <summary>Vector index name to use.</summary>
    private readonly string _vectorIndexName;

    /// <summary>Full text search index name to use.</summary>
    private readonly string _fullTextSearchIndexName;

    /// <summary>Number of max retries for vector collection operation.</summary>
    private readonly int _maxRetries;

    /// <summary>Delay in milliseconds between retries for vector collection operation.</summary>
    private readonly int _delayInMilliseconds;

    /// <summary>Number of nearest neighbors to use during the vector search.</summary>
    private readonly int? _numCandidates;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</param>
    /// <param name="name">The name of the collection that this <see cref="MongoCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate MongoDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate MongoDynamicCollection instead.")]
    public MongoCollection(
        IMongoDatabase mongoDatabase,
        string name,
        MongoCollectionOptions? options = default)
        : this(
            mongoDatabase,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(MongoDynamicCollection)))
                : new MongoModelBuilder().Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator),
            options)
    {
    }

    internal MongoCollection(IMongoDatabase mongoDatabase, string name, Func<MongoCollectionOptions, CollectionModel> modelFactory, MongoCollectionOptions? options)
    {
        // Verify.
        Verify.NotNull(mongoDatabase);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        options ??= MongoCollectionOptions.Default;

        // Assign.
        this._mongoDatabase = mongoDatabase;
        this._mongoCollection = mongoDatabase.GetCollection<BsonDocument>(name);
        this.Name = name;
        this._model = modelFactory(options);

        this._vectorIndexName = options.VectorIndexName;
        this._fullTextSearchIndexName = options.FullTextSearchIndexName;
        this._maxRetries = options.MaxRetries;
        this._delayInMilliseconds = options.DelayInMilliseconds;
        this._numCandidates = options.NumCandidates;

        this._mapper = typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? (new MongoDynamicMapper(this._model) as IMongoMapper<TRecord>)!
            : new MongoMapper<TRecord>(this._model);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = MongoConstants.VectorStoreSystemName,
            VectorStoreName = mongoDatabase.DatabaseNamespace?.DatabaseName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("ListCollectionNames", () => this.InternalCollectionExistsAsync(cancellationToken));

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        // The IMongoDatabase.CreateCollectionAsync "Creates a new collection if not already available".
        // So for EnsureCollectionExistsAsync, we don't perform an additional check.
        await this.RunOperationAsync("CreateCollection",
            () => this._mongoDatabase.CreateCollectionAsync(this.Name, cancellationToken: cancellationToken)).ConfigureAwait(false);

        await this.RunOperationWithRetryAsync(
            "CreateIndexes",
            this._maxRetries,
            this._delayInMilliseconds,
            () => this.CreateIndexesAsync(this.Name, cancellationToken),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        await this.RunOperationAsync("DeleteOne", () => this._mongoCollection.DeleteOneAsync(this.GetFilterById(stringKey), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var stringKeys = keys is IEnumerable<string> k ? k : keys.Cast<string>();

        await this.RunOperationAsync("DeleteMany", () => this._mongoCollection.DeleteManyAsync(this.GetFilterByIds(stringKeys), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("DropCollection", () => this._mongoDatabase.DropCollectionAsync(this.Name, cancellationToken));

    /// <inheritdoc />
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        using var cursor = await this
            .FindAsync(this.GetFilterById(stringKey), top: 1, skip: null, includeVectors, sortDefinition: null, cancellationToken)
            .ConfigureAwait(false);

        var record = await cursor.SingleOrDefaultAsync(cancellationToken).ConfigureAwait(false);

        if (record is null)
        {
            return default;
        }

        return this._mapper.MapFromStorageToDataModel(record, includeVectors);
    }

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        RecordRetrievalOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var stringKeys = keys is IEnumerable<string> k ? k : keys.Cast<string>();

        using var cursor = await this
            .FindAsync(this.GetFilterByIds(stringKeys), top: null, skip: null, includeVectors, sortDefinition: null, cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var record in cursor.Current)
            {
                if (record is not null)
                {
                    yield return this._mapper.MapFromStorageToDataModel(record, includeVectors);
                }
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

        var i = 0;

        foreach (var record in records)
        {
            await this.UpsertCoreAsync(record, i++, generatedEmbeddings, cancellationToken).ConfigureAwait(false);
        }
    }

    private async Task UpsertCoreAsync(TRecord record, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings, CancellationToken cancellationToken = default)
    {
        const string OperationName = "ReplaceOne";

        var replaceOptions = new ReplaceOptions { IsUpsert = true };
        var storageModel = this._mapper.MapFromDataToStorageModel(record, recordIndex, generatedEmbeddings);

        var key = storageModel[MongoConstants.MongoReservedKeyPropertyName].AsString;

        await this.RunOperationAsync(OperationName, async () =>
            await this._mongoCollection
                .ReplaceOneAsync(this.GetFilterById(key), storageModel, replaceOptions, cancellationToken)
                .ConfigureAwait(false)).ConfigureAwait(false);
    }

    private static async ValueTask<(IEnumerable<TRecord> records, IReadOnlyList<Embedding>?[]?)> ProcessEmbeddingsAsync(
        CollectionModel model,
        IEnumerable<TRecord> records,
        CancellationToken cancellationToken)
    {
        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = model.VectorProperties[i];

            if (MongoModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
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
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await floatTask.ConfigureAwait(false);
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
        MEVD.VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
        var vectorArray = await GetSearchVectorArrayAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = options.Skip + top;

        var numCandidates = this._numCandidates ?? itemsAmount * MongoConstants.DefaultNumCandidatesRatio;

        var searchQuery = MongoCollectionSearchMapping.GetSearchQuery(
            vectorArray,
            this._vectorIndexName,
            vectorProperty.StorageName,
            itemsAmount,
            numCandidates,
            filter);

        var projectionQuery = MongoCollectionSearchMapping.GetProjectionQuery(
            ScorePropertyName,
            DocumentPropertyName);

        BsonDocument[] pipeline = [searchQuery, projectionQuery];

        const string OperationName = "Aggregate";
        using var cursor = await this.RunOperationWithRetryAsync(
            OperationName,
            this._maxRetries,
            this._delayInMilliseconds,
            () => this._mongoCollection.AggregateAsync<BsonDocument>(pipeline, cancellationToken: cancellationToken),
            cancellationToken).ConfigureAwait(false);

        using var errorHandlingAsyncCursor = new ErrorHandlingAsyncCursor<BsonDocument>(cursor, this._collectionMetadata, OperationName);
        var mappedResults = this.EnumerateAndMapSearchResultsAsync(errorHandlingAsyncCursor, options.Skip, options.IncludeVectors, cancellationToken);

        await foreach (var result in mappedResults.ConfigureAwait(false))
        {
            yield return result;
        }
    }

    private static async ValueTask<float[]> GetSearchVectorArrayAsync<TInput>(TInput searchValue, VectorPropertyModel vectorProperty, CancellationToken cancellationToken)
        where TInput : notnull
    {
        if (searchValue is float[] array)
        {
            return array;
        }

        var memory = searchValue switch
        {
            ReadOnlyMemory<float> r => r,
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), MongoModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

        return MemoryMarshal.TryGetArray(memory, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length
                ? segment.Array
                : memory.ToArray();
    }

    #endregion Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(
        Expression<Func<TRecord, bool>> filter,
        int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        // Translate the filter now, so if it fails, we throw immediately.
        var translatedFilter = new MongoFilterTranslator().Translate(filter, this._model);
        SortDefinition<BsonDocument>? sortDefinition = null;
        var orderBy = options.OrderBy?.Invoke(new()).Values;
        if (orderBy is { Count: > 0 })
        {
            sortDefinition = Builders<BsonDocument>.Sort.Combine(
                orderBy.Select(pair =>
                {
                    var storageName = this._model.GetDataOrKeyProperty(pair.PropertySelector).StorageName;

                    return pair.Ascending
                        ? Builders<BsonDocument>.Sort.Ascending(storageName)
                        : Builders<BsonDocument>.Sort.Descending(storageName);
                }));
        }

        using IAsyncCursor<BsonDocument> cursor = await this.FindAsync(
            translatedFilter,
            top,
            options.Skip,
            options.IncludeVectors,
            sortDefinition,
            cancellationToken).ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var response in cursor.Current)
            {
                var record = this._mapper.MapFromStorageToDataModel(response, options.IncludeVectors);

                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(TInput searchValue, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        Verify.NotLessThan(top, 1);

        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var vectorArray = await GetSearchVectorArrayAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = options.Skip + top;

        var numCandidates = this._numCandidates ?? itemsAmount * MongoConstants.DefaultNumCandidatesRatio;

        BsonDocument[] pipeline = MongoCollectionSearchMapping.GetHybridSearchPipeline(
            vectorArray,
            keywords,
            this.Name,
            this._vectorIndexName,
            this._fullTextSearchIndexName,
            vectorProperty.StorageName,
            textDataProperty.StorageName,
            ScorePropertyName,
            DocumentPropertyName,
            itemsAmount,
            numCandidates,
            filter);

        var results = await this.RunOperationWithRetryAsync(
            "KeywordVectorizedHybridSearch",
            this._maxRetries,
            this._delayInMilliseconds,
            async () =>
            {
                var cursor = await this._mongoCollection
                    .AggregateAsync<BsonDocument>(pipeline, cancellationToken: cancellationToken)
                    .ConfigureAwait(false);

                return this.EnumerateAndMapSearchResultsAsync(cursor, options.Skip, options.IncludeVectors, cancellationToken);
            },
            cancellationToken).ConfigureAwait(false);

        await foreach (var result in results.ConfigureAwait(false))
        {
            yield return result;
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(IMongoDatabase) ? this._mongoDatabase :
            serviceType == typeof(IMongoCollection<BsonDocument>) ? this._mongoCollection :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    #region private

    private async Task CreateIndexesAsync(string collectionName, CancellationToken cancellationToken)
    {
        var indexCursor = await this._mongoCollection.Indexes.ListAsync(cancellationToken).ConfigureAwait(false);
        var indexes = indexCursor.ToList(cancellationToken).Select(index => index["name"].ToString()) ?? [];

        var indexArray = new BsonArray();

        // Create the vector index config if the index does not exist
        if (!indexes.Contains(this._vectorIndexName))
        {
            var fieldsArray = new BsonArray();

            fieldsArray.AddRange(MongoCollectionCreateMapping.GetVectorIndexFields(this._model.VectorProperties));
            fieldsArray.AddRange(MongoCollectionCreateMapping.GetFilterableDataIndexFields(this._model.DataProperties));

            if (fieldsArray.Count > 0)
            {
                indexArray.Add(new BsonDocument
                {
                    { "name", this._vectorIndexName },
                    { "type", "vectorSearch" },
                    { "definition", new BsonDocument { ["fields"] = fieldsArray } },
                });
            }
        }

        // Create the full text search index config if the index does not exist
        if (!indexes.Contains(this._fullTextSearchIndexName))
        {
            var fieldsDocument = new BsonDocument();

            fieldsDocument.AddRange(MongoCollectionCreateMapping.GetFullTextSearchableDataIndexFields(this._model.DataProperties));

            if (fieldsDocument.ElementCount > 0)
            {
                indexArray.Add(new BsonDocument
                {
                    { "name", this._fullTextSearchIndexName },
                    { "type", "search" },
                    {
                        "definition", new BsonDocument
                        {
                            ["mappings"] = new BsonDocument
                            {
                                ["dynamic"] = false,
                                ["fields"] = fieldsDocument
                            }
                        }
                    },
                });
            }
        }

        // Create any missing indexes.
        if (indexArray.Count > 0)
        {
            var createIndexCommand = new BsonDocument
            {
                { "createSearchIndexes", collectionName },
                { "indexes", indexArray }
            };

            await this._mongoDatabase.RunCommandAsync<BsonDocument>(createIndexCommand, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
    }

    private async Task<IAsyncCursor<BsonDocument>> FindAsync(
        FilterDefinition<BsonDocument> filter,
        int? top,
        int? skip,
        bool includeVectors,
        SortDefinition<BsonDocument>? sortDefinition,
        CancellationToken cancellationToken)
    {
        const string OperationName = "Find";

        ProjectionDefinitionBuilder<BsonDocument> projectionBuilder = Builders<BsonDocument>.Projection;
        ProjectionDefinition<BsonDocument>? projectionDefinition = null;

        if (!includeVectors)
        {
            foreach (var vectorPropertyName in this._model.VectorProperties)
            {
                projectionDefinition = projectionDefinition is not null ?
                    projectionDefinition.Exclude(vectorPropertyName.StorageName) :
                    projectionBuilder.Exclude(vectorPropertyName.StorageName);
            }
        }

        var findOptions = projectionDefinition is not null ?
            new FindOptions<BsonDocument> { Projection = projectionDefinition, Limit = top, Skip = skip, Sort = sortDefinition } :
            new FindOptions<BsonDocument> { Limit = top, Skip = skip, Sort = sortDefinition };

        var cursor = await this.RunOperationAsync(OperationName, () =>
            this._mongoCollection.FindAsync(filter, findOptions, cancellationToken)).ConfigureAwait(false);

        return new ErrorHandlingAsyncCursor<BsonDocument>(cursor, this._collectionMetadata, OperationName);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> EnumerateAndMapSearchResultsAsync(
        IAsyncCursor<BsonDocument> cursor,
        int skip,
        bool includeVectors,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var skipCounter = 0;

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var response in cursor.Current)
            {
                if (skipCounter >= skip)
                {
                    var score = response[ScorePropertyName].AsDouble;
                    var record = this._mapper.MapFromStorageToDataModel(response[DocumentPropertyName].AsBsonDocument, includeVectors);

                    yield return new VectorSearchResult<TRecord>(record, score);
                }

                skipCounter++;
            }
        }
    }

    private FilterDefinition<BsonDocument> GetFilterById(string id)
        => Builders<BsonDocument>.Filter.Eq(document => document[MongoConstants.MongoReservedKeyPropertyName], id);

    private FilterDefinition<BsonDocument> GetFilterByIds(IEnumerable<string> ids)
        => Builders<BsonDocument>.Filter.In(document => document[MongoConstants.MongoReservedKeyPropertyName].AsString, ids);

    private async Task<bool> InternalCollectionExistsAsync(CancellationToken cancellationToken)
    {
        var filter = new BsonDocument("name", this.Name);
        var options = new ListCollectionNamesOptions { Filter = filter };

        using var cursor = await this._mongoDatabase.ListCollectionNamesAsync(options, cancellationToken: cancellationToken).ConfigureAwait(false);

        return await cursor.AnyAsync(cancellationToken).ConfigureAwait(false);
    }

    private Task RunOperationAsync(string operationName, Func<Task> operation)
        => VectorStoreErrorHandler.RunOperationAsync<MongoException>(this._collectionMetadata, operationName, operation);

    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
        => VectorStoreErrorHandler.RunOperationAsync<T, MongoException>(this._collectionMetadata, operationName, operation);

    private Task RunOperationWithRetryAsync(
        string operationName,
        int maxRetries,
        int delayInMilliseconds,
        Func<Task> operation,
        CancellationToken cancellationToken)
        => VectorStoreErrorHandler.RunOperationWithRetryAsync<MongoException>(
            this._collectionMetadata,
            operationName,
            maxRetries,
            delayInMilliseconds,
            operation,
            cancellationToken);

    private async Task<T> RunOperationWithRetryAsync<T>(
        string operationName,
        int maxRetries,
        int delayInMilliseconds,
        Func<Task<T>> operation,
        CancellationToken cancellationToken)
        => await VectorStoreErrorHandler.RunOperationWithRetryAsync<T, MongoException>(
            this._collectionMetadata,
            operationName,
            maxRetries,
            delayInMilliseconds,
            operation,
            cancellationToken).ConfigureAwait(false);

    private string GetStringKey(TKey key)
    {
        Verify.NotNull(key);

        var stringKey = key as string ?? throw new UnreachableException("string key should have been validated during model building");

        Verify.NotNullOrWhiteSpace(stringKey, nameof(key));

        return stringKey;
    }

    #endregion
}
