// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Azure CosmosDB Mongo vCore database.
/// Get more details about Azure Cosmos Mongo vCore vector search  https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search
/// </summary>
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
public class AzureCosmosDBMongoDBMemoryStore : IMemoryStore, IDisposable
{
    private readonly MongoClient _mongoClient;
    private readonly IMongoDatabase _mongoDatabase;
    private readonly AzureCosmosDBMongoDBConfig _config;
    private readonly bool _ownsMongoClient;

    /// <summary>
    /// Initiates a AzureCosmosDBMongoDBMemoryStore instance using a Azure CosmosDB Mongo vCore connection string
    /// and other properties required for vector search.
    /// </summary>
    /// <param name="connectionString">Connection string required to connect to Azure Cosmos Mongo vCore.</param>
    /// <param name="databaseName">Database name for Mongo vCore DB</param>
    /// <param name="config">Azure CosmosDB MongoDB Config containing specific parameters for vector search.</param>
    public AzureCosmosDBMongoDBMemoryStore(
        string connectionString,
        string databaseName,
        AzureCosmosDBMongoDBConfig config
    )
    {
        MongoClientSettings settings = MongoClientSettings.FromConnectionString(connectionString);
        this._config = config;
        settings.ApplicationName = this._config.ApplicationName;
        this._mongoClient = new MongoClient(settings);
        this._mongoDatabase = this._mongoClient.GetDatabase(databaseName);
        this._ownsMongoClient = true;
    }

    /// <summary>
    /// Initiates a AzureCosmosDBMongoDBMemoryStore instance using a Azure CosmosDB MongoDB client
    /// and other properties required for vector search.
    /// </summary>
    public AzureCosmosDBMongoDBMemoryStore(
        MongoClient mongoClient,
        string databaseName,
        AzureCosmosDBMongoDBConfig config
    )
    {
        this._config = config;
        this._mongoClient = mongoClient;
        this._mongoDatabase = this._mongoClient.GetDatabase(databaseName);
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(
        string collectionName,
        CancellationToken cancellationToken = default
    )
    {
        await this
            ._mongoDatabase.CreateCollectionAsync(
                collectionName,
                cancellationToken: cancellationToken
            )
            .ConfigureAwait(false);
        var indexes = await this.GetCollection(collectionName)
            .Indexes.ListAsync(cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        if (!indexes.ToList(cancellationToken: cancellationToken).Any(index => index["name"] == this._config.IndexName))
        {
            var command = new BsonDocument();
            switch (this._config.Kind)
            {
                case AzureCosmosDBVectorSearchType.VectorIVF:
                    command = this.GetIndexDefinitionVectorIVF(collectionName);
                    break;
                case AzureCosmosDBVectorSearchType.VectorHNSW:
                    command = this.GetIndexDefinitionVectorHNSW(collectionName);
                    break;
            }
            await this
                ._mongoDatabase.RunCommandAsync<BsonDocument>(
                    command,
                    cancellationToken: cancellationToken
                )
                .ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync(
        [EnumeratorCancellation] CancellationToken cancellationToken = default
    )
    {
        using var cursor = await this
            ._mongoDatabase.ListCollectionNamesAsync(cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var name in cursor.Current)
            {
                yield return name;
            }
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(
        string collectionName,
        CancellationToken cancellationToken = default
    )
    {
        await foreach (
            var existingCollectionName in this.GetCollectionsAsync(cancellationToken)
                .ConfigureAwait(false)
        )
        {
            if (existingCollectionName == collectionName)
            {
                return true;
            }
        }
        return false;
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(
        string collectionName,
        CancellationToken cancellationToken = default
    ) => this._mongoDatabase.DropCollectionAsync(collectionName, cancellationToken);

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(
        string collectionName,
        MemoryRecord record,
        CancellationToken cancellationToken = default
    )
    {
        record.Key = record.Metadata.Id;

        var replaceOptions = new ReplaceOptions() { IsUpsert = true };

        var result = await this.GetCollection(collectionName)
            .ReplaceOneAsync(
                GetFilterById(record.Metadata.Id),
                new AzureCosmosDBMongoDBMemoryRecord(record),
                replaceOptions,
                cancellationToken
            )
            .ConfigureAwait(false);

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default
    )
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(collectionName, record, cancellationToken)
                .ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(
        string collectionName,
        string key,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default
    )
    {
        using var cursor = await this.GetCollection(collectionName)
            .FindAsync(GetFilterById(key), null, cancellationToken)
            .ConfigureAwait(false);

        var cosmosRecord = await cursor
            .SingleOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
        var result = cosmosRecord?.ToMemoryRecord(withEmbedding);

        return result;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default
    )
    {
        using var cursor = await this.GetCollection(collectionName)
            .FindAsync(GetFilterByIds(keys), null, cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var cosmosRecord in cursor.Current)
            {
                yield return cosmosRecord.ToMemoryRecord(withEmbeddings);
            }
        }
    }

    /// <inheritdoc/>
    public Task RemoveAsync(
        string collectionName,
        string key,
        CancellationToken cancellationToken = default
    ) => this.GetCollection(collectionName).DeleteOneAsync(GetFilterById(key), cancellationToken);

    /// <inheritdoc/>
    public Task RemoveBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        CancellationToken cancellationToken = default
    ) =>
        this.GetCollection(collectionName).DeleteManyAsync(GetFilterByIds(keys), cancellationToken);

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default
    )
    {
        using var cursor = await this.VectorSearchAsync(
                1,
                embedding,
                collectionName,
                cancellationToken
            )
            .ConfigureAwait(false);
        var result = await cursor.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
        // Access the similarityScore from the BSON document
        double similarityScore = result.GetValue("similarityScore").AsDouble;
        if (similarityScore < minRelevanceScore)
        {
            return null;
        }

        MemoryRecord memoryRecord = AzureCosmosDBMongoDBMemoryRecord.ToMemoryRecord(
            result["document"].AsBsonDocument,
            withEmbedding
        );
        return (memoryRecord, similarityScore);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default
    )
    {
        using var cursor = await this.VectorSearchAsync(
                limit,
                embedding,
                collectionName,
                cancellationToken
            )
            .ConfigureAwait(false);
        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var doc in cursor.Current)
            {
                // Access the similarityScore from the BSON document
                var similarityScore = doc.GetValue("similarityScore").AsDouble;
                if (similarityScore < minRelevanceScore)
                {
                    continue;
                }

                MemoryRecord memoryRecord = AzureCosmosDBMongoDBMemoryRecord.ToMemoryRecord(
                    doc["document"].AsBsonDocument,
                    withEmbeddings
                );
                yield return (memoryRecord, similarityScore);
            }
        }
    }

    /// <summary>
    /// Disposes the <see cref="AzureCosmosDBMongoDBMemoryStore"/> instance.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the resources used by the <see cref="AzureCosmosDBMongoDBMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._ownsMongoClient)
            {
                this._mongoClient.Cluster.Dispose();
            }
        }
    }

    private BsonDocument GetIndexDefinitionVectorIVF(string collectionName)
    {
        return new BsonDocument
        {
            { "createIndexes", collectionName },
            {
                "indexes",
                new BsonArray
                {
                    new BsonDocument
                    {
                        { "name", this._config.IndexName },
                        {
                            "key",
                            new BsonDocument { { "embedding", "cosmosSearch" } }
                        },
                        {
                            "cosmosSearchOptions",
                            new BsonDocument
                            {
                                { "kind", this._config.Kind.GetCustomName() },
                                { "numLists", this._config.NumLists },
                                { "similarity", this._config.Similarity.GetCustomName() },
                                { "dimensions", this._config.Dimensions }
                            }
                        }
                    }
                }
            }
        };
    }

    private BsonDocument GetIndexDefinitionVectorHNSW(string collectionName)
    {
        return new BsonDocument
        {
            { "createIndexes", collectionName },
            {
                "indexes",
                new BsonArray
                {
                    new BsonDocument
                    {
                        { "name", this._config.IndexName },
                        {
                            "key",
                            new BsonDocument { { "embedding", "cosmosSearch" } }
                        },
                        {
                            "cosmosSearchOptions",
                            new BsonDocument
                            {
                                { "kind", this._config.Kind.GetCustomName() },
                                { "m", this._config.NumberOfConnections },
                                { "efConstruction", this._config.EfConstruction },
                                { "similarity", this._config.Similarity.GetCustomName() },
                                { "dimensions", this._config.Dimensions }
                            }
                        }
                    }
                }
            }
        };
    }

    private async Task<IAsyncCursor<BsonDocument>> VectorSearchAsync(
        int limit,
        ReadOnlyMemory<float> embedding,
        string collectionName,
        CancellationToken cancellationToken
    )
    {
        if (limit <= 0)
        {
            limit = int.MaxValue;
        }

        BsonDocument[] pipeline = [];
        switch (this._config.Kind)
        {
            case AzureCosmosDBVectorSearchType.VectorIVF:
                pipeline = this.GetVectorIVFSearchPipeline(embedding, limit);
                break;
            case AzureCosmosDBVectorSearchType.VectorHNSW:
                pipeline = this.GetVectorHNSWSearchPipeline(embedding, limit);
                break;
        }

        var cursor = await this.GetCollection(collectionName)
            .AggregateAsync<BsonDocument>(pipeline, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
        return cursor;
    }

    private BsonDocument[] GetVectorIVFSearchPipeline(ReadOnlyMemory<float> embedding, int limit)
    {
        string searchStage =
            @"
        {
            ""$search"": {
                ""cosmosSearch"": {
                    ""vector"": ["
            + string.Join(
                ",",
                embedding.ToArray().Select(f => f.ToString(CultureInfo.InvariantCulture))
            )
            + @"],
                    ""path"": ""embedding"",
                    ""k"": "
            + limit
            + @"
                },
                ""returnStoredSource"": true
            }
        }";

        string projectStage =
            """
            {
                "$project": {
                    "similarityScore": { "$meta": "searchScore" },
                    "document": "$$ROOT"
                }
            }
            """;

        BsonDocument searchBson = BsonDocument.Parse(searchStage);
        BsonDocument projectBson = BsonDocument.Parse(projectStage);
        return [searchBson, projectBson];
    }

    private BsonDocument[] GetVectorHNSWSearchPipeline(ReadOnlyMemory<float> embedding, int limit)
    {
        string searchStage =
            @"
        {
            ""$search"": {
                ""cosmosSearch"": {
                    ""vector"": ["
            + string.Join(
                ",",
                embedding.ToArray().Select(f => f.ToString(CultureInfo.InvariantCulture))
            )
            + @"],
                    ""path"": ""embedding"",
                    ""k"": "
            + limit
            + @",
                    ""efSearch"": "
            + this._config.EfSearch
            + @"
                }
            }
        }";

        string projectStage = """
            {
                "$project": {
                    "similarityScore": { "$meta": "searchScore" },
                    "document": "$$ROOT"
                }
            }
            """;

        BsonDocument searchBson = BsonDocument.Parse(searchStage);
        BsonDocument projectBson = BsonDocument.Parse(projectStage);
        return [searchBson, projectBson];
    }

    private IMongoCollection<AzureCosmosDBMongoDBMemoryRecord> GetCollection(
        string collectionName
    ) => this._mongoDatabase.GetCollection<AzureCosmosDBMongoDBMemoryRecord>(collectionName);

    private static FilterDefinition<AzureCosmosDBMongoDBMemoryRecord> GetFilterById(string id) =>
        Builders<AzureCosmosDBMongoDBMemoryRecord>.Filter.Eq(m => m.Id, id);

    private static FilterDefinition<AzureCosmosDBMongoDBMemoryRecord> GetFilterByIds(
        IEnumerable<string> ids
    ) => Builders<AzureCosmosDBMongoDBMemoryRecord>.Filter.In(m => m.Id, ids);
}
