﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure CosmosDB MongoDB as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class AzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord> where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "AzureCosmosDBMongoDB";

    /// <summary>Property name to be used for search similarity score value.</summary>
    private const string ScorePropertyName = "similarityScore";

    /// <summary>Property name to be used for search document value.</summary>
    private const string DocumentPropertyName = "document";

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</summary>
    private readonly IMongoDatabase _mongoDatabase;

    /// <summary>Azure CosmosDB MongoDB collection to perform record operations.</summary>
    private readonly IMongoCollection<BsonDocument> _mongoCollection;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord> _options;

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
    /// Initializes a new instance of the <see cref="AzureCosmosDBMongoDBVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureCosmosDBMongoDBVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public AzureCosmosDBMongoDBVectorStoreRecordCollection(
        IMongoDatabase mongoDatabase,
        string collectionName,
        AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(mongoDatabase);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.BsonDocumentCustomMapper is not null, AzureCosmosDBMongoDBConstants.SupportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._mongoDatabase = mongoDatabase;
        this._mongoCollection = mongoDatabase.GetCollection<BsonDocument>(collectionName);
        this.CollectionName = collectionName;
        this._options = options ?? new AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), this._options.VectorStoreRecordDefinition, new() { RequiresAtLeastOneVector = false, SupportsMultipleKeys = false, SupportsMultipleVectors = true });

        this._storagePropertyNames = GetStoragePropertyNames(this._propertyReader.Properties, typeof(TRecord));

        // Use Mongo reserved key property name as storage key property name
        this._storagePropertyNames[this._propertyReader.KeyPropertyName] = AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName;

        this._vectorStoragePropertyNames = this._propertyReader.VectorProperties.Select(property => this._storagePropertyNames[property.DataModelPropertyName]).ToList();

        this._mapper = this.InitializeMapper();
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("ListCollectionNames", () => this.InternalCollectionExistsAsync(cancellationToken));

    /// <inheritdoc />
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        await this.RunOperationAsync("CreateCollection",
            () => this._mongoDatabase.CreateCollectionAsync(this.CollectionName, cancellationToken: cancellationToken)).ConfigureAwait(false);

        await this.RunOperationAsync("CreateIndexes",
            () => this.CreateIndexesAsync(this.CollectionName, cancellationToken: cancellationToken)).ConfigureAwait(false);
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
    public async Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        await this.RunOperationAsync("DeleteOne", () => this._mongoCollection.DeleteOneAsync(this.GetFilterById(key), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        await this.RunOperationAsync("DeleteMany", () => this._mongoCollection.DeleteManyAsync(this.GetFilterByIds(keys), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("DropCollection", () => this._mongoDatabase.DropCollectionAsync(this.CollectionName, cancellationToken));

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
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
            return null;
        }

        return VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromStorageToDataModel(record, new() { IncludeVectors = includeVectors }));
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
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
    public Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        const string OperationName = "ReplaceOne";

        var replaceOptions = new ReplaceOptions { IsUpsert = true };
        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        var key = storageModel[AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName].AsString;

        return this.RunOperationAsync(OperationName, async () =>
        {
            await this._mongoCollection
                .ReplaceOneAsync(this.GetFilterById(key), storageModel, replaceOptions, cancellationToken)
                .ConfigureAwait(false);

            return key;
        });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.UpsertAsync(record, options, cancellationToken));
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
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        Array vectorArray = vector switch
        {
            ReadOnlyMemory<float> memoryFloat => memoryFloat.ToArray(),
            ReadOnlyMemory<double> memoryDouble => memoryDouble.ToArray(),
            _ => throw new NotSupportedException(
                $"The provided vector type {vector.GetType().FullName} is not supported by the Azure CosmosDB for MongoDB connector. " +
                $"Supported types are: {string.Join(", ", [
                    typeof(ReadOnlyMemory<float>).FullName,
                    typeof(ReadOnlyMemory<double>).FullName])}")
        };

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this.GetVectorPropertyForSearch(searchOptions.VectorPropertyName);

        if (vectorProperty is null)
        {
            throw new InvalidOperationException("The collection does not have any vector properties, so vector search is not possible.");
        }

        var vectorPropertyName = this._storagePropertyNames[vectorProperty.DataModelPropertyName];

        var filter = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(
            searchOptions.Filter,
            this._storagePropertyNames);

        // Constructing a query to fetch "skip + top" total items
        // to perform skip logic locally, since skip option is not part of API. 
        var itemsAmount = searchOptions.Skip + searchOptions.Top;

        var searchQuery = vectorProperty.IndexKind switch
        {
            IndexKind.Hnsw => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetSearchQueryForHnswIndex(
                vectorArray,
                vectorPropertyName,
                itemsAmount,
                this._options.EfSearch,
                filter),
            IndexKind.IvfFlat => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetSearchQueryForIvfIndex(
                vectorArray,
                vectorPropertyName,
                itemsAmount,
                filter),
            _ => throw new InvalidOperationException(
                $"Index kind '{vectorProperty.IndexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore. " +
                $"Supported index kinds are: {string.Join(", ", [IndexKind.Hnsw, IndexKind.IvfFlat])}")
        };

        var projectionQuery = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetProjectionQuery(
            ScorePropertyName,
            DocumentPropertyName);

        BsonDocument[] pipeline = [searchQuery, projectionQuery];

        var cursor = await this._mongoCollection
            .AggregateAsync<BsonDocument>(pipeline, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        return new VectorSearchResults<TRecord>(this.EnumerateAndMapSearchResultsAsync(cursor, searchOptions, cancellationToken));
    }

    #region private

    private async Task CreateIndexesAsync(string collectionName, CancellationToken cancellationToken)
    {
        var indexCursor = await this._mongoCollection.Indexes.ListAsync(cancellationToken).ConfigureAwait(false);
        var indexes = indexCursor.ToList(cancellationToken).Select(index => index["name"].ToString()) ?? [];
        var uniqueIndexes = new HashSet<string?>(indexes);

        var indexArray = new BsonArray();

        indexArray.AddRange(AzureCosmosDBMongoDBVectorStoreCollectionCreateMapping.GetVectorIndexes(
            this._propertyReader.VectorProperties,
            this._storagePropertyNames,
            uniqueIndexes,
            this._options.NumLists,
            this._options.EfConstruction));

        indexArray.AddRange(AzureCosmosDBMongoDBVectorStoreCollectionCreateMapping.GetFilterableDataIndexes(
            this._propertyReader.DataProperties,
            this._storagePropertyNames,
            uniqueIndexes));

        if (indexArray.Count > 0)
        {
            var createIndexCommand = new BsonDocument
            {
                { "createIndexes", collectionName },
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
        VectorSearchOptions searchOptions,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "Aggregate";

        var skipCounter = 0;

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var response in cursor.Current)
            {
                if (skipCounter >= searchOptions.Skip)
                {
                    var score = response[ScorePropertyName].AsDouble;
                    var record = VectorStoreErrorHandler.RunModelConversion(
                        DatabaseName,
                        this.CollectionName,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(response[DocumentPropertyName].AsBsonDocument, new()));

                    yield return new VectorSearchResult<TRecord>(record, score);
                }

                skipCounter++;
            }
        }
    }

    private FilterDefinition<BsonDocument> GetFilterById(string id)
        => Builders<BsonDocument>.Filter.Eq(document => document[AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName], id);

    private FilterDefinition<BsonDocument> GetFilterByIds(IEnumerable<string> ids)
        => Builders<BsonDocument>.Filter.In(document => document[AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName].AsString, ids);

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
            return (new AzureCosmosDBMongoDBGenericDataModelMapper(this._propertyReader.RecordDefinition) as IVectorStoreRecordMapper<TRecord, BsonDocument>)!;
        }

        return new AzureCosmosDBMongoDBVectorStoreRecordMapper<TRecord>(this._propertyReader);
    }

    #endregion
}
