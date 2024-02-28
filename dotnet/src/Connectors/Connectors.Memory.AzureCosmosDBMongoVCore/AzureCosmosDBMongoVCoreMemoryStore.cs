// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCosmosDBMongoVCore;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Azure CosmosDB Mongo vCore database.
/// </summary>
public class AzureCosmosDBMongoVCoreMemoryStore: IMemoryStore, IDisposable
{
    private readonly IMongoClient _cosmosDBMongoClient;
    private readonly IMongoDatabase _cosmosMongoDatabase;
    private readonly IMongoCollection _cosmosMongoCollection;
    private readonly String _collectionName;
    private readonly String -indexName;
    private readonly String _kind;
    private readonly int _numLists;
    private readonly String _similarity;
    private readonly int _dimensions;
    private readonly int _numberOfConnections;
    private readonly int _efConstruction;
    private readonly int _efSearch;


    public AzureCosmosDBMongoVCoreMemoryStore(
        string connectionString,
        string databaseName,
        string? indexName = default,
        string? kind = "vector_hnsw",
        int? numLists = 1, 
        string? similarity = "COS",
        int? dimensions = 3,
        int? numberOfConnections = 16,
        int? efConstruction = 64,
        int? efSearch = 40)
    {
        this._cosmosDBMongoClient = new MongoClient(connectionString);
        this._cosmosMongoDatabase = this._cosmosDBMongoClient.GetDatabase(databaseName);
        this._indexName = indexName;
        this._kind = kind;
        this._numLists = numLists;
        this._similarity = similarity;
        this._dimensions = dimensions;
        this._numberOfConnections = numberOfConnections;
        this._efConstruction = efConstruction;
        this._efSearch = efSearch;
    }

    public AzureCosmosDBMongoVCoreMemoryStore(
        IMongoClient mongoClient,
        string databaseName,
        string? indexName = default,
        string? kind = "vector_hnsw",
        int? numLists = 1, 
        string? similarity = "COS",
        int? dimensions = 3,
        int? numberOfConnections = 16,
        int? efConstruction = 64,
        int? efSearch = 40)
    {
        this._cosmosDBMongoClient = mongoClient
        this._cosmosMongoDatabase = this._cosmosDBMongoClient.GetDatabase(databaseName);
        this._indexName = indexName;
        this._kind = kind;
        this._numLists = numLists;
        this._similarity = similarity;
        this._dimensions = dimensions;
        this._numberOfConnections = numberOfConnections;
        this._efConstruction = efConstruction;
        this._efSearch = efSearch;
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._cosmosMongoDatabase.CreateCollectionAsync(collectionName, cancellationToken);

        if (!this._cosmosMongoDatabase.GetCollection<BsonDocument>(collectionName).Indexes.ToList().contains(this._indexName)) 
        {
            var command;
            switch(this._kind)
            {
                case "vector-ivf":
                    command = GetIndexDefinitionVectorIVF(collectionName)
                    break;
                case "vector-hnsw":
                    command = GetIndexDefinitionVectorHNSW(collectionName)
                    break;  
            }
            await _cosmosMongoDatabase.RunCommandAsync<BsonDocument>(command);
        }
    }

    private BsonDocument GetIndexDefinitionVectorIVF(string collectionName)
    {
        return new BsonDocument
            {
                { "createIndexes", this.collectionName },
                {
                    "indexes",
                    new BsonArray
                    {
                        new BsonDocument
                        {
                            { "name", this._indexName },
                            { "key", new BsonDocument { { "embedding", "cosmosSearch" } } },
                            { "cosmosSearchOptions", new BsonDocument
                                {
                                    { "kind", this._kind },
                                    { "numLists", this._numLists },
                                    { "similarity", this._similarity },
                                    { "dimensions", this._dimensions}
                                }
                            }
                        }
                    }
                }
            };
    }

    private BsonDocument GetIndexDefinitionVectorHNSW(string index)
    {
        return new BsonDocument
        {
            { "createIndexes", this.collectionName },
            {
                "indexes",
                new BsonArray
                {
                    new BsonDocument
                    {
                        { "name", this._indexName },
                        { "key", new BsonDocument { { "embedding", "cosmosSearch" } } },
                        { "cosmosSearchOptions", new BsonDocument
                            {
                                { "kind", this._kind },
                                { "m", this._numberOfConnections },
                                { "efConstruction", this._efConstruction},
                                { "similarity", this._similarity },
                                { "dimensions", this._dimensions}
                            }
                        }
                    }
                }
            }
        }; 
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default) => 
        this._cosmosMongoDatabase.GetCollection<BsonDocument>(this._collectionName);
    
    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        collectionNames = await this._mongoDatabase.ListCollectionNamesAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        await foreach ( var existingCollectionName in collectionNames)
        {
            if (existingCollectionName == collectionName)
            {
                return true;
            }
        }

        return false;
    }

     /// <inheritdoc/>
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default) =>
        this._mongoDatabase.DropCollectionAsync(collectionName, cancellationToken);   

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        record.key = record.Metadata.Id;
        var filter = Builders<AzureCosmosDBMongoVCoreMemoryRecord>.Filter.Eq(m => m.Id, record.Key);

        var replaceOptions = new ReplaceOptions() { IsUpsert = true };

        var result = await this._cosmosMongoDatabase.GetCollection<AzureCosmosDBMongoVCoreMemoryRecord>(collectionName)
            .ReplaceOneAsync(filter, new AzureCosmosDBMongoVCoreMemoryRecord(record), replaceOptions, cancellationToken)
            .ConfigureAwait(false);

        return record.Key;
    }    

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var collection = this._cosmosMongoDatabase.GetCollection<AzureCosmosDBMongoVCoreMemoryRecord>(collectionName);
        AzureCosmosDBMongoVCoreMemoryRecord azureCosmosDBMongoVCoreMemoryRecord = await collection.FindAsync(GetFilterById(key), new FindOptions(), cancellationToken);
        var result = azureCosmosDBMongoVCoreMemoryRecord?.ToMemoryRecord(withEmbedding);

        return result;
    }    

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach(var key in keys)
        {
            yield return await this.GetAsync(collectionName, key, withEmbeddings, cancellationToken)
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return GetNearestMatchesAsync(collectionName, embedding, 1, minRelevanceScore, withEmbeddings, cancellationToken);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (limit <= 0) { limit=int.MaxValue;}

        var pipeline;
            switch (this._config.GetKind)
            {
                case "vector-ivf":
                    pipeline = GetVectorIVFSearchPipeline(embedding, limit)
                    break;
                case "vector-hnsw":
                    pipeline = GetVectorHNSWSearchPipeline(embedding, limit)
                    break;    
            }

        await foreach (AzureCosmosDBMongoVCoreMemoryRecord doc in this._cosmosMongoCollection.AggregateAsync<BsonDocument>(pipeline))
        {
            if (doc == null || doc.similarityScore < minRelevanceScore) { continue; }

            MemoryRecord memoryRecord = doc.Document.ToMemoryRecord(withEmbeddings);

            yield return (memoryRecord, doc.similarityScore);
        }
    }

    private BsonDocument GetVectorIVFSearchPipeline(string embedding, int limit)
    {
        return new List<BsonDocument>
        {
            new BsonDocument
            {
                { "$search", new BsonDocument
                    {
                        { "cosmosSearch", new BsonDocument
                            {
                                { "vector", embedding.ToList() },
                                { "path", "embedding" },
                                { "k", limit }
                            }
                        },
                        { "returnStoredSource", true }
                    }
                }
            },
            new BsonDocument
            {
                { "$project", new BsonDocument
                    {
                        { "similarityScore", new BsonDocument { { "$meta", "searchScore" } } },
                        { "document", "$$ROOT" }
                    }
                }
            }
        };  
    }

    private BsonDocument GetVectorHNSWSearchPipeline(string embedding, int limit)
    {
        return new List<BsonDocument>
        {
            new BsonDocument
            {
                { "$search", new BsonDocument
                    {
                        "cosmosSearch", new BsonDocument
                        {
                            { "vector", embedding.ToList() },
                            { "path", "embedding" },
                            { "k", limit },
                            { "efSearch", this._config.GetEfSearch}
                        }
                    }
                }
            }
        };
    }

    /// <inheritdoc/>
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default) =>
        this._cosmosMongoDatabase.GetCollection<AzureCosmosDBMongoVCoreMemoryRecord>(collectionName)
        .DeleteOneAsync(GetFilterById(key), cancellationToken);

    /// <inheritdoc/>
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default) =>
         this._cosmosMongoDatabase.GetCollection<AzureCosmosDBMongoVCoreMemoryRecord>(collectionName)
         .DeleteManyAsync(GetFilterByIds(keys), cancellationToken);    

    private static FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord> GetFilterById(string id) =>
        Builders<AzureCosmosDBMongoVCoreMemoryRecord>.Filter.Eq(m => m.Id, id);

    private static FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord> GetFilterByIds(IEnumerable<string> ids) =>
        Builders<AzureCosmosDBMongoVCoreMemoryRecord>.Filter.In(m => m.Id, ids);
}