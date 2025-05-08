// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;
using MongoDB.Bson;
using MongoDB.Driver;
using MEVD = Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Service for storing and retrieving vector records, that uses MongoDB as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be either <see cref="string"/>, or <see cref="object"/> for dynamic mapping.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class MongoDBVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>, IKeywordHybridSearch<TRecord>
    where TKey : notnull
    where TRecord : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

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

    /// <summary>Optional configuration options for this class.</summary>
    private readonly MongoDBVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>Interface for mapping between a storage model, and the consumer record data model.</summary>
    private readonly IMongoDBMapper<TRecord> _mapper;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <inheritdoc />
    public string Name { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</param>
    /// <param name="name">The name of the collection that this <see cref="MongoDBVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public MongoDBVectorStoreRecordCollection(
        IMongoDatabase mongoDatabase,
        string name,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(mongoDatabase);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported (and object for dynamic mapping)");
        }

        // Assign.
        this._mongoDatabase = mongoDatabase;
        this._mongoCollection = mongoDatabase.GetCollection<BsonDocument>(name);
        this.Name = name;
        this._options = options ?? new MongoDBVectorStoreRecordCollectionOptions<TRecord>();
        this._model = new MongoDBModelBuilder().Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, this._options.EmbeddingGenerator);
        this._mapper = typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? (new MongoDBDynamicDataModelMapper(this._model) as IMongoDBMapper<TRecord>)!
            : new MongoDBVectorStoreRecordMapper<TRecord>(this._model);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
            VectorStoreName = mongoDatabase.DatabaseNamespace?.DatabaseName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("ListCollectionNames", () => this.InternalCollectionExistsAsync(cancellationToken));

    /// <inheritdoc />
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // The IMongoDatabase.CreateCollectionAsync "Creates a new collection if not already available".
        // To make sure that all the connectors are consistent, we throw when the collection exists.
        if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            throw new VectorStoreOperationException("Collection already exists.")
            {
                VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "CreateCollection"
            };
        }

        await this.CreateCollectionIfNotExistsAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        // The IMongoDatabase.CreateCollectionAsync "Creates a new collection if not already available".
        // So for CreateCollectionIfNotExistsAsync, we don't perform an additional check.
        await this.RunOperationAsync("CreateCollection",
            () => this._mongoDatabase.CreateCollectionAsync(this.Name, cancellationToken: cancellationToken)).ConfigureAwait(false);

        await this.RunOperationWithRetryAsync(
            "CreateIndexes",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
            () => this.CreateIndexesAsync(this.Name, cancellationToken),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        await this.RunOperationAsync("DeleteOne", () => this._mongoCollection.DeleteOneAsync(this.GetFilterById(stringKey), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var stringKeys = keys is IEnumerable<string> k ? k : keys.Cast<string>();

        await this.RunOperationAsync("DeleteMany", () => this._mongoCollection.DeleteManyAsync(this.GetFilterByIds(stringKeys), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("DropCollection", () => this._mongoDatabase.DropCollectionAsync(this.Name, cancellationToken));

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Find";

        var stringKey = this.GetStringKey(key);

        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var record = await this.RunOperationAsync(OperationName, async () =>
        {
            using var cursor = await this
                .FindAsync(this.GetFilterById(stringKey), options, cancellationToken)
                .ConfigureAwait(false);

            return await cursor.SingleOrDefaultAsync(cancellationToken).ConfigureAwait(false);
        }).ConfigureAwait(false);

        if (record is null)
        {
            return default;
        }

        return VectorStoreErrorHandler.RunModelConversion(
            MongoDBConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            OperationName,
            () => this._mapper.MapFromStorageToDataModel(record, new() { IncludeVectors = includeVectors }));
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "Find";

        if (options?.IncludeVectors == true && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var stringKeys = keys is IEnumerable<string> k ? k : keys.Cast<string>();

        using var cursor = await this
            .FindAsync(this.GetFilterByIds(stringKeys), options, cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var record in cursor.Current)
            {
                if (record is not null)
                {
                    yield return VectorStoreErrorHandler.RunModelConversion(
                        MongoDBConstants.VectorStoreSystemName,
                        this._collectionMetadata.VectorStoreName,
                        this.Name,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(record, new()));
                }
            }
        }
    }

    /// <inheritdoc />
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        const string OperationName = "ReplaceOne";

        Embedding?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>, ReadOnlyMemory<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new Embedding?[vectorPropertyCount];
                generatedEmbeddings[i] = await floatTask.ConfigureAwait(false);
            }
            else if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<double>, ReadOnlyMemory<double>>(record, cancellationToken, out var doubleTask))
            {
                generatedEmbeddings ??= new Embedding?[vectorPropertyCount];
                generatedEmbeddings[i] = await doubleTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var replaceOptions = new ReplaceOptions { IsUpsert = true };
        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            MongoDBConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record, generatedEmbeddings));

        var key = storageModel[MongoDBConstants.MongoReservedKeyPropertyName].AsString;

        return await this.RunOperationAsync(OperationName, async () =>
        {
            await this._mongoCollection
                .ReplaceOneAsync(this.GetFilterById(key), storageModel, replaceOptions, cancellationToken)
                .ConfigureAwait(false);

            return (TKey)(object)key;
        }).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.UpsertAsync(record, cancellationToken));
        var results = await Task.WhenAll(tasks).ConfigureAwait(false);
        return results.Where(r => r is not null).ToList();
    }

    #region Search

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        MEVD.VectorSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
            {
                var embedding = await generator.GenerateAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }

            case IEmbeddingGenerator<TInput, Embedding<double>> generator:
            {
                var embedding = await generator.GenerateAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    MongoDBConstants.SupportedVectorTypes.Contains(typeof(TInput))
                        ? string.Format(VectorDataStrings.EmbeddingTypePassedToSearchAsync)
                        : string.Format(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType, typeof(TInput).Name, vectorProperty.EmbeddingGenerator.GetType().Name));
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        MEVD.VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        string operationName,
        MEVD.VectorSearchOptions<TRecord> options,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Array vectorArray = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoDBFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = options.Skip + top;

        var numCandidates = this._options.NumCandidates ?? itemsAmount * MongoDBConstants.DefaultNumCandidatesRatio;

        var searchQuery = MongoDBVectorStoreCollectionSearchMapping.GetSearchQuery(
            vectorArray,
            this._options.VectorIndexName,
            vectorProperty.StorageName,
            itemsAmount,
            numCandidates,
            filter);

        var projectionQuery = MongoDBVectorStoreCollectionSearchMapping.GetProjectionQuery(
            ScorePropertyName,
            DocumentPropertyName);

        BsonDocument[] pipeline = [searchQuery, projectionQuery];

        var results = await this.RunOperationWithRetryAsync(
            "VectorizedSearch",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
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
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, MEVD.VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    #endregion Search

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        GetFilteredRecordOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        // Translate the filter now, so if it fails, we throw immediately.
        var translatedFilter = new MongoDBFilterTranslator().Translate(filter, this._model);
        SortDefinition<BsonDocument>? sortDefinition = null;
        if (options.OrderBy.Values.Count > 0)
        {
            sortDefinition = Builders<BsonDocument>.Sort.Combine(
                options.OrderBy.Values.Select(pair =>
                {
                    var storageName = this._model.GetDataOrKeyProperty(pair.PropertySelector).StorageName;

                    return pair.Ascending
                        ? Builders<BsonDocument>.Sort.Ascending(storageName)
                        : Builders<BsonDocument>.Sort.Descending(storageName);
                }));
        }

        using IAsyncCursor<BsonDocument> cursor = await this.RunOperationWithRetryAsync(
            "GetAsync",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
            async () =>
            {
                return await this._mongoCollection.FindAsync(translatedFilter,
                    new()
                    {
                        Limit = top,
                        Skip = options.Skip,
                        Sort = sortDefinition
                    },
                    cancellationToken: cancellationToken).ConfigureAwait(false);
            },
            cancellationToken).ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var response in cursor.Current)
            {
                var record = VectorStoreErrorHandler.RunModelConversion(
                    MongoDBConstants.VectorStoreSystemName,
                    this._collectionMetadata.VectorStoreName,
                    this.Name,
                    "GetAsync",
                    () => this._mapper.MapFromStorageToDataModel(response, new() { IncludeVectors = options.IncludeVectors }));

                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Array vectorArray = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoDBFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = options.Skip + top;

        var numCandidates = this._options.NumCandidates ?? itemsAmount * MongoDBConstants.DefaultNumCandidatesRatio;

        BsonDocument[] pipeline = MongoDBVectorStoreCollectionSearchMapping.GetHybridSearchPipeline(
            vectorArray,
            keywords,
            this.Name,
            this._options.VectorIndexName,
            this._options.FullTextSearchIndexName,
            vectorProperty.StorageName,
            textDataProperty.StorageName,
            ScorePropertyName,
            DocumentPropertyName,
            itemsAmount,
            numCandidates,
            filter);

        var results = await this.RunOperationWithRetryAsync(
            "KeywordVectorizedHybridSearch",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
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
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
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
        if (!indexes.Contains(this._options.VectorIndexName))
        {
            var fieldsArray = new BsonArray();

            fieldsArray.AddRange(MongoDBVectorStoreCollectionCreateMapping.GetVectorIndexFields(this._model.VectorProperties));
            fieldsArray.AddRange(MongoDBVectorStoreCollectionCreateMapping.GetFilterableDataIndexFields(this._model.DataProperties));

            if (fieldsArray.Count > 0)
            {
                indexArray.Add(new BsonDocument
                {
                    { "name", this._options.VectorIndexName },
                    { "type", "vectorSearch" },
                    { "definition", new BsonDocument { ["fields"] = fieldsArray } },
                });
            }
        }

        // Create the full text search index config if the index does not exist
        if (!indexes.Contains(this._options.FullTextSearchIndexName))
        {
            var fieldsDocument = new BsonDocument();

            fieldsDocument.AddRange(MongoDBVectorStoreCollectionCreateMapping.GetFullTextSearchableDataIndexFields(this._model.DataProperties));

            if (fieldsDocument.ElementCount > 0)
            {
                indexArray.Add(new BsonDocument
                {
                    { "name", this._options.FullTextSearchIndexName },
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

    private async Task<IAsyncCursor<BsonDocument>> FindAsync(FilterDefinition<BsonDocument> filter, GetRecordOptions? options, CancellationToken cancellationToken)
    {
        ProjectionDefinitionBuilder<BsonDocument> projectionBuilder = Builders<BsonDocument>.Projection;
        ProjectionDefinition<BsonDocument>? projectionDefinition = null;

        var includeVectors = options?.IncludeVectors ?? false;

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
            new FindOptions<BsonDocument> { Projection = projectionDefinition } :
            null;

        return await this._mongoCollection.FindAsync(filter, findOptions, cancellationToken).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> EnumerateAndMapSearchResultsAsync(
        IAsyncCursor<BsonDocument> cursor,
        int skip,
        bool includeVectors,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "Aggregate";

        var skipCounter = 0;

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var response in cursor.Current)
            {
                if (skipCounter >= skip)
                {
                    var score = response[ScorePropertyName].AsDouble;
                    var record = VectorStoreErrorHandler.RunModelConversion(
                        MongoDBConstants.VectorStoreSystemName,
                        this._collectionMetadata.VectorStoreName,
                        this.Name,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(response[DocumentPropertyName].AsBsonDocument, new() { IncludeVectors = includeVectors }));

                    yield return new VectorSearchResult<TRecord>(record, score);
                }

                skipCounter++;
            }
        }
    }

    private FilterDefinition<BsonDocument> GetFilterById(string id)
        => Builders<BsonDocument>.Filter.Eq(document => document[MongoDBConstants.MongoReservedKeyPropertyName], id);

    private FilterDefinition<BsonDocument> GetFilterByIds(IEnumerable<string> ids)
        => Builders<BsonDocument>.Filter.In(document => document[MongoDBConstants.MongoReservedKeyPropertyName].AsString, ids);

    private async Task<bool> InternalCollectionExistsAsync(CancellationToken cancellationToken)
    {
        var filter = new BsonDocument("name", this.Name);
        var options = new ListCollectionNamesOptions { Filter = filter };

        using var cursor = await this._mongoDatabase.ListCollectionNamesAsync(options, cancellationToken: cancellationToken).ConfigureAwait(false);

        return await cursor.AnyAsync(cancellationToken).ConfigureAwait(false);
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
                VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
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
                VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }
    }

    private async Task RunOperationWithRetryAsync(
        string operationName,
        int maxRetries,
        int delayInMilliseconds,
        Func<Task> operation,
        CancellationToken cancellationToken)
    {
        var retries = 0;

        while (retries < maxRetries)
        {
            try
            {
                await operation.Invoke().ConfigureAwait(false);
                return;
            }
            catch (Exception ex)
            {
                retries++;

                if (retries >= maxRetries)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", ex)
                    {
                        VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
                        VectorStoreName = this._collectionMetadata.VectorStoreName,
                        CollectionName = this.Name,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    private async Task<T> RunOperationWithRetryAsync<T>(
        string operationName,
        int maxRetries,
        int delayInMilliseconds,
        Func<Task<T>> operation,
        CancellationToken cancellationToken)
    {
        var retries = 0;

        while (retries < maxRetries)
        {
            try
            {
                return await operation.Invoke().ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                retries++;

                if (retries >= maxRetries)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", ex)
                    {
                        VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
                        VectorStoreName = this._collectionMetadata.VectorStoreName,
                        CollectionName = this.Name,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
        }

        throw new VectorStoreOperationException("Retry logic failed.");
    }

    private static Array VerifyVectorParam<TVector>(TVector vector)
    {
        Verify.NotNull(vector);

        return vector switch
        {
            ReadOnlyMemory<float> memoryFloat => memoryFloat.ToArray(),
            ReadOnlyMemory<double> memoryDouble => memoryDouble.ToArray(),
            _ => throw new NotSupportedException(
                $"The provided vector type {vector.GetType().FullName} is not supported by the MongoDB connector. " +
                $"Supported types are: {string.Join(", ", [
                    typeof(ReadOnlyMemory<float>).FullName,
                    typeof(ReadOnlyMemory<double>).FullName])}")
        };
    }

    private string GetStringKey(TKey key)
    {
        Verify.NotNull(key);

        var stringKey = key as string ?? throw new UnreachableException("string key should have been validated during model building");

        Verify.NotNullOrWhiteSpace(stringKey, nameof(key));

        return stringKey;
    }

    #endregion
}
