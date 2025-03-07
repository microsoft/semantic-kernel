// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Driver;
using MEVD = Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Service for storing and retrieving vector records, that uses MongoDB as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class MongoDBVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord>, IKeywordHybridSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "MongoDB";

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
    private readonly IVectorStoreRecordMapper<TRecord, BsonDocument> _mapper;

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>Collection of vector storage property names.</summary>
    private readonly List<string> _vectorStoragePropertyNames;

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="MongoDBVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public MongoDBVectorStoreRecordCollection(
        IMongoDatabase mongoDatabase,
        string collectionName,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(mongoDatabase);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.BsonDocumentCustomMapper is not null, MongoDBConstants.SupportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._mongoDatabase = mongoDatabase;
        this._mongoCollection = mongoDatabase.GetCollection<BsonDocument>(collectionName);
        this.CollectionName = collectionName;
        this._options = options ?? new MongoDBVectorStoreRecordCollectionOptions<TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), this._options.VectorStoreRecordDefinition, new() { RequiresAtLeastOneVector = false, SupportsMultipleKeys = false, SupportsMultipleVectors = true });

        this._storagePropertyNames = GetStoragePropertyNames(this._propertyReader.Properties, typeof(TRecord));

        // Use Mongo reserved key property name as storage key property name
        this._storagePropertyNames[this._propertyReader.KeyPropertyName] = MongoDBConstants.MongoReservedKeyPropertyName;

        this._vectorStoragePropertyNames = this._propertyReader.VectorProperties.Select(property => this._storagePropertyNames[property.DataModelPropertyName]).ToList();

        this._mapper = this.InitializeMapper();
    }

    /// <inheritdoc />
    public virtual Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("ListCollectionNames", () => this.InternalCollectionExistsAsync(cancellationToken));

    /// <inheritdoc />
    public virtual async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
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
    public virtual async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public virtual async Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        await this.RunOperationAsync("DeleteOne", () => this._mongoCollection.DeleteOneAsync(this.GetFilterById(key), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public virtual async Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        await this.RunOperationAsync("DeleteMany", () => this._mongoCollection.DeleteManyAsync(this.GetFilterByIds(keys), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public virtual Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("DropCollection", () => this._mongoDatabase.DropCollectionAsync(this.CollectionName, cancellationToken));

    /// <inheritdoc />
    public virtual async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        const string OperationName = "Find";

        var includeVectors = options?.IncludeVectors ?? false;

        var record = await this.RunOperationAsync(OperationName, async () =>
        {
            using var cursor = await this
                .FindAsync(this.GetFilterById(key), options, cancellationToken)
                .ConfigureAwait(false);

            return await cursor.SingleOrDefaultAsync(cancellationToken).ConfigureAwait(false);
        }).ConfigureAwait(false);

        if (record is null)
        {
            return default;
        }

        return VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromStorageToDataModel(record, new() { IncludeVectors = includeVectors }));
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<string> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "Find";

        using var cursor = await this
            .FindAsync(this.GetFilterByIds(keys), options, cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var record in cursor.Current)
            {
                if (record is not null)
                {
                    yield return VectorStoreErrorHandler.RunModelConversion(
                        DatabaseName,
                        this.CollectionName,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(record, new()));
                }
            }
        }
    }

    /// <inheritdoc />
    public virtual Task<string> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        const string OperationName = "ReplaceOne";

        var replaceOptions = new ReplaceOptions { IsUpsert = true };
        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        var key = storageModel[MongoDBConstants.MongoReservedKeyPropertyName].AsString;

        return this.RunOperationAsync(OperationName, async () =>
        {
            await this._mongoCollection
                .ReplaceOneAsync(this.GetFilterById(key), storageModel, replaceOptions, cancellationToken)
                .ConfigureAwait(false);

            return key;
        });
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.UpsertAsync(record, cancellationToken));
        var results = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var result in results)
        {
            if (result is not null)
            {
                yield return result;
            }
        }
    }

    /// <inheritdoc />
    public virtual async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        MEVD.VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
    {
        Array vectorArray = VerifyVectorParam(vector);

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(searchOptions);
        var vectorPropertyName = this._storagePropertyNames[vectorProperty.DataModelPropertyName];

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = searchOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._storagePropertyNames),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoDBFilterTranslator().Translate(newFilter, this._storagePropertyNames),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API.
        var itemsAmount = searchOptions.Skip + searchOptions.Top;

        var numCandidates = this._options.NumCandidates ?? itemsAmount * MongoDBConstants.DefaultNumCandidatesRatio;

        var searchQuery = MongoDBVectorStoreCollectionSearchMapping.GetSearchQuery(
            vectorArray,
            this._options.VectorIndexName,
            vectorPropertyName,
            itemsAmount,
            numCandidates,
            filter);

        var projectionQuery = MongoDBVectorStoreCollectionSearchMapping.GetProjectionQuery(
            ScorePropertyName,
            DocumentPropertyName);

        BsonDocument[] pipeline = [searchQuery, projectionQuery];

        return await this.RunOperationWithRetryAsync(
            "VectorizedSearch",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
            async () =>
            {
                var cursor = await this._mongoCollection
                    .AggregateAsync<BsonDocument>(pipeline, cancellationToken: cancellationToken)
                    .ConfigureAwait(false);

                return new VectorSearchResults<TRecord>(this.EnumerateAndMapSearchResultsAsync(cursor, searchOptions.Skip, searchOptions.IncludeVectors, cancellationToken));
            },
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Array vectorArray = VerifyVectorParam(vector);

        var searchOptions = options ?? s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = searchOptions.VectorProperty });
        var vectorPropertyName = this._storagePropertyNames[vectorProperty.DataModelPropertyName];
        var textDataProperty = this._propertyReader.GetFullTextDataPropertyOrSingle(searchOptions.AdditionalProperty);
        var textDataPropertyName = this._storagePropertyNames[textDataProperty.DataModelPropertyName];

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = searchOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(legacyFilter, this._storagePropertyNames),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new MongoDBFilterTranslator().Translate(newFilter, this._storagePropertyNames),
            _ => null
        };
#pragma warning restore CS0618

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API. 
        var itemsAmount = searchOptions.Skip + searchOptions.Top;

        var numCandidates = this._options.NumCandidates ?? itemsAmount * MongoDBConstants.DefaultNumCandidatesRatio;

        BsonDocument[] pipeline = MongoDBVectorStoreCollectionSearchMapping.GetHybridSearchPipeline(
            vectorArray,
            keywords,
            this.CollectionName,
            this._options.VectorIndexName,
            this._options.FullTextSearchIndexName,
            vectorPropertyName,
            textDataPropertyName,
            ScorePropertyName,
            DocumentPropertyName,
            itemsAmount,
            numCandidates,
            filter);

        return await this.RunOperationWithRetryAsync(
            "KeywordVectorizedHybridSearch",
            this._options.MaxRetries,
            this._options.DelayInMilliseconds,
            async () =>
            {
                var cursor = await this._mongoCollection
                    .AggregateAsync<BsonDocument>(pipeline, cancellationToken: cancellationToken)
                    .ConfigureAwait(false);

                return new VectorSearchResults<TRecord>(this.EnumerateAndMapSearchResultsAsync(cursor, searchOptions.Skip, searchOptions.IncludeVectors, cancellationToken));
            },
            cancellationToken).ConfigureAwait(false);
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

            fieldsArray.AddRange(MongoDBVectorStoreCollectionCreateMapping.GetVectorIndexFields(
                this._propertyReader.VectorProperties,
                this._storagePropertyNames));

            fieldsArray.AddRange(MongoDBVectorStoreCollectionCreateMapping.GetFilterableDataIndexFields(
                this._propertyReader.DataProperties,
                this._storagePropertyNames));

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

            fieldsDocument.AddRange(MongoDBVectorStoreCollectionCreateMapping.GetFullTextSearchableDataIndexFields(
                this._propertyReader.DataProperties,
                this._storagePropertyNames));

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

        if (!includeVectors && this._vectorStoragePropertyNames.Count > 0)
        {
            foreach (var vectorPropertyName in this._vectorStoragePropertyNames)
            {
                projectionDefinition = projectionDefinition is not null ?
                    projectionDefinition.Exclude(vectorPropertyName) :
                    projectionBuilder.Exclude(vectorPropertyName);
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
                        DatabaseName,
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
                VectorStoreType = DatabaseName,
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
                VectorStoreType = DatabaseName,
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
                        VectorStoreType = DatabaseName,
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
                        VectorStoreType = DatabaseName,
                        CollectionName = this.CollectionName,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
        }

        throw new VectorStoreOperationException("Retry logic failed.");
    }

    /// <summary>
    /// Gets storage property names taking into account BSON serialization attributes.
    /// </summary>
    private static Dictionary<string, string> GetStoragePropertyNames(
        IReadOnlyList<VectorStoreRecordProperty> properties,
        Type dataModel)
    {
        var storagePropertyNames = new Dictionary<string, string>();

        foreach (var property in properties)
        {
            var propertyInfo = dataModel.GetProperty(property.DataModelPropertyName);
            string propertyName;

            if (propertyInfo != null)
            {
                var bsonElementAttribute = propertyInfo.GetCustomAttribute<BsonElementAttribute>();

                propertyName = bsonElementAttribute?.ElementName ?? property.DataModelPropertyName;
            }
            else
            {
                propertyName = property.DataModelPropertyName;
            }

            storagePropertyNames[property.DataModelPropertyName] = propertyName;
        }

        return storagePropertyNames;
    }

    /// <summary>
    /// Returns custom mapper, generic data model mapper or default record mapper.
    /// </summary>
    private IVectorStoreRecordMapper<TRecord, BsonDocument> InitializeMapper()
    {
        if (this._options.BsonDocumentCustomMapper is not null)
        {
            return this._options.BsonDocumentCustomMapper;
        }

        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>))
        {
            return (new MongoDBGenericDataModelMapper(this._propertyReader.RecordDefinition) as IVectorStoreRecordMapper<TRecord, BsonDocument>)!;
        }

        return new MongoDBVectorStoreRecordMapper<TRecord>(this._propertyReader);
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
    #endregion
}
