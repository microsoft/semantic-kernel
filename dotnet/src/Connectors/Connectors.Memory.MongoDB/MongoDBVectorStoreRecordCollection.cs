// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
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
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private readonly IVectorStoreRecordMapper<TRecord, BsonDocument> _mapper;
#pragma warning restore CS0618

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="MongoDBVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public MongoDBVectorStoreRecordCollection(
        IMongoDatabase mongoDatabase,
        string collectionName,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(mongoDatabase);
        Verify.NotNullOrWhiteSpace(collectionName);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported (and object for dynamic mapping)");
        }

        // Assign.
        this._mongoDatabase = mongoDatabase;
        this._mongoCollection = mongoDatabase.GetCollection<BsonDocument>(collectionName);
        this.CollectionName = collectionName;
        this._options = options ?? new MongoDBVectorStoreRecordCollectionOptions<TRecord>();
        this._model = new MongoDBModelBuilder().Build(typeof(TRecord), this._options.VectorStoreRecordDefinition);
        this._mapper = this.InitializeMapper();

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
            VectorStoreName = mongoDatabase.DatabaseNamespace?.DatabaseName,
            CollectionName = collectionName
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
                CollectionName = this.CollectionName,
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
            () => this._mongoDatabase.CreateCollectionAsync(this.CollectionName, cancellationToken: cancellationToken)).ConfigureAwait(false);

        await this.RunOperationWithRetryAsync(
            "CreateIndexes",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
            () => this.CreateIndexesAsync(this.CollectionName, cancellationToken),
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
        => this.RunOperationAsync("DropCollection", () => this._mongoDatabase.DropCollectionAsync(this.CollectionName, cancellationToken));

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Find";

        var stringKey = this.GetStringKey(key);

        var includeVectors = options?.IncludeVectors ?? false;

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
            this.CollectionName,
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
                        this.CollectionName,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(record, new()));
                }
            }
        }
    }

    /// <inheritdoc />
    public Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        const string OperationName = "ReplaceOne";

        var replaceOptions = new ReplaceOptions { IsUpsert = true };
        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            MongoDBConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        var key = storageModel[MongoDBConstants.MongoReservedKeyPropertyName].AsString;

        return this.RunOperationAsync(OperationName, async () =>
        {
            await this._mongoCollection
                .ReplaceOneAsync(this.GetFilterById(key), storageModel, replaceOptions, cancellationToken)
                .ConfigureAwait(false);

            return (TKey)(object)key;
        });
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.UpsertAsync(record, cancellationToken));
        var results = await Task.WhenAll(tasks).ConfigureAwait(false);
        return results.Where(r => r is not null).ToList();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        int top,
        MEVD.VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Array vectorArray = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(searchOptions);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = searchOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoDBFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = searchOptions.Skip + top;

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

                return this.EnumerateAndMapSearchResultsAsync(cursor, searchOptions.Skip, searchOptions.IncludeVectors, cancellationToken);
            },
            cancellationToken).ConfigureAwait(false);

        await foreach (var result in results.ConfigureAwait(false))
        {
            yield return result;
        }
    }

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
                    this.CollectionName,
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

        var searchOptions = options ?? s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = searchOptions.VectorProperty });
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(searchOptions.AdditionalProperty);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = searchOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoDBFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = searchOptions.Skip + top;

        var numCandidates = this._options.NumCandidates ?? itemsAmount * MongoDBConstants.DefaultNumCandidatesRatio;

        BsonDocument[] pipeline = MongoDBVectorStoreCollectionSearchMapping.GetHybridSearchPipeline(
            vectorArray,
            keywords,
            this.CollectionName,
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

                return this.EnumerateAndMapSearchResultsAsync(cursor, searchOptions.Skip, searchOptions.IncludeVectors, cancellationToken);
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
                        this.CollectionName,
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
        var filter = new BsonDocument("name", this.CollectionName);
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
                VectorStoreSystemName = MongoDBConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.CollectionName,
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
                        CollectionName = this.CollectionName,
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
                        CollectionName = this.CollectionName,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
        }

        throw new VectorStoreOperationException("Retry logic failed.");
    }

#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    /// <summary>
    /// Returns custom mapper, generic data model mapper or default record mapper.
    /// </summary>
    private IVectorStoreRecordMapper<TRecord, BsonDocument> InitializeMapper()
    {
        if (this._options.BsonDocumentCustomMapper is not null)
        {
            return this._options.BsonDocumentCustomMapper;
        }

        if (typeof(TRecord) == typeof(Dictionary<string, object?>))
        {
            return (new MongoDBDynamicDataModelMapper(this._model) as IVectorStoreRecordMapper<TRecord, BsonDocument>)!;
        }

        return new MongoDBVectorStoreRecordMapper<TRecord>(this._model);
    }
#pragma warning restore CS0618

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
