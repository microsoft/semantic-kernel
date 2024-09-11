﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
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

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</summary>
    private readonly IMongoDatabase _mongoDatabase;

    /// <summary>Azure CosmosDB MongoDB collection to perform record operations.</summary>
    private readonly IMongoCollection<BsonDocument> _mongoCollection;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>Interface for mapping between a storage model, and the consumer record data model.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, BsonDocument> _mapper;

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>Collection of vector storage property names.</summary>
    private readonly List<string> _vectorStoragePropertyNames;

    /// <summary>Collection of record vector properties.</summary>
    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

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

        // Assign.
        this._mongoDatabase = mongoDatabase;
        this._mongoCollection = mongoDatabase.GetCollection<BsonDocument>(collectionName);
        this.CollectionName = collectionName;
        this._options = options ?? new AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>();
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);

        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(
            typeof(TRecord).Name,
            this._vectorStoreRecordDefinition,
            supportsMultipleVectors: true,
            requiresAtLeastOneVector: false);

        this._storagePropertyNames = GetStoragePropertyNames(properties, typeof(TRecord));
        this._vectorProperties = properties.VectorProperties;
        this._vectorStoragePropertyNames = this._vectorProperties.Select(property => this._storagePropertyNames[property.DataModelPropertyName]).ToList();

        this._mapper = this._options.BsonDocumentCustomMapper ??
            new AzureCosmosDBMongoDBVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition, this._storagePropertyNames);
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("ListCollectionNames", () => this.InternalCollectionExistsAsync(cancellationToken));

    /// <inheritdoc />
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        await this.RunOperationAsync("CreateCollection",
            () => this._mongoDatabase.CreateCollectionAsync(this.CollectionName, cancellationToken: cancellationToken)).ConfigureAwait(false);

        await this.RunOperationAsync("CreateIndex",
            () => this.CreateIndexAsync(this.CollectionName, cancellationToken: cancellationToken)).ConfigureAwait(false);
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
            () => this._mapper.MapFromStorageToDataModel(record, new()));
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

    #region private

    private async Task CreateIndexAsync(string collectionName, CancellationToken cancellationToken)
    {
        var indexCursor = await this._mongoCollection.Indexes.ListAsync(cancellationToken).ConfigureAwait(false);
        var indexes = indexCursor.ToList(cancellationToken).Select(index => index["name"].ToString()) ?? [];
        var uniqueIndexes = new HashSet<string?>(indexes);

        var indexArray = new BsonArray();

        // Create separate index for each vector property
        foreach (var property in this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordVectorProperty>())
        {
            // Use index name same as vector property name with underscore
            var vectorPropertyName = this._storagePropertyNames[property.DataModelPropertyName];
            var indexName = $"{vectorPropertyName}_";

            // If index already exists, proceed to the next vector property
            if (uniqueIndexes.Contains(indexName))
            {
                continue;
            }

            // Otherwise, create a new index
            var searchOptions = new BsonDocument
            {
                { "kind", GetIndexKind(property.IndexKind, vectorPropertyName) },
                { "numLists", this._options.NumLists },
                { "similarity", GetDistanceFunction(property.DistanceFunction, vectorPropertyName) },
                { "dimensions", property.Dimensions }
            };

            if (this._options.EfConstruction is not null)
            {
                searchOptions["efConstruction"] = this._options.EfConstruction;
            }

            var indexDocument = new BsonDocument
            {
                ["name"] = indexName,
                ["key"] = new BsonDocument { [vectorPropertyName] = "cosmosSearch" },
                ["cosmosSearchOptions"] = searchOptions
            };

            indexArray.Add(indexDocument);
        }

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
    /// More information about Azure CosmosDB for MongoDB index kinds here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search" />.
    /// </summary>
    private static string GetIndexKind(string? indexKind, string vectorPropertyName)
    {
        return indexKind switch
        {
            IndexKind.Hnsw => "vector-hnsw",
            IndexKind.IvfFlat => "vector-ivf",
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore.")
        };
    }

    /// <summary>
    /// More information about Azure CosmosDB for MongoDB distance functions here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search" />.
    /// </summary>
    private static string GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
    {
        return distanceFunction switch
        {
            DistanceFunction.CosineDistance => "COS",
            DistanceFunction.DotProductSimilarity => "IP",
            DistanceFunction.EuclideanDistance => "L2",
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore.")
        };
    }

    /// <summary>
    /// Gets storage property names taking into account BSON serialization attributes.
    /// </summary>
    private static Dictionary<string, string> GetStoragePropertyNames(
        (VectorStoreRecordKeyProperty KeyProperty, List<VectorStoreRecordDataProperty> DataProperties, List<VectorStoreRecordVectorProperty> VectorProperties) properties,
        Type dataModel)
    {
        var storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties);

        var allProperties = new List<VectorStoreRecordProperty>([properties.KeyProperty])
            .Concat(properties.DataProperties)
            .Concat(properties.VectorProperties);

        foreach (var property in allProperties)
        {
            var propertyInfo = dataModel.GetProperty(property.DataModelPropertyName);

            if (propertyInfo != null)
            {
                var bsonElementAttribute = propertyInfo.GetCustomAttribute<BsonElementAttribute>();
                if (bsonElementAttribute is not null)
                {
                    storagePropertyNames[property.DataModelPropertyName] = bsonElementAttribute.ElementName;
                }
            }
        }

        return storagePropertyNames;
    }

    #endregion
}
