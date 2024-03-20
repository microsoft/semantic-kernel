// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Configuration;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoVCore;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Azure CosmosDB Mongo vCore database.
/// Get more details about Azure Cosmos Mongo vCore vector search  https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search
/// </summary>
public class AzureCosmosDBMongoVCoreMemoryStore : IMemoryStore, IDisposable
{
    private readonly IMongoClient _cosmosDBMongoClient;
    private readonly IMongoDatabase _cosmosMongoDatabase;

    /// <summary>
    /// Index name for the Mongo vCore DB
    /// </summary>
    private readonly String _indexName;
    private readonly String _kind;
    private readonly int _numLists;
    private readonly String _similarity;
    private readonly int _dimensions;
    private readonly int _numberOfConnections;
    private readonly int _efConstruction;
    private readonly int _efSearch;

    /// <summary>
    /// Initiates a AzureCosmosDBMongoVCoreMemoryStore instance.
    /// <summary>
    /// <param name="connectionString">Connection string required to connect to Azure Cosmos Mongo vCore.</param>
    /// <param name="databaseName">Database name for Mongo vCore DB</param>
    /// <param name="indexName">Index name for the Mongo vCore DB</param>
    /// <param name="applicationName">Application name for the client for tracking and logging</param>
    /// <param name="kind">Kind: Type of vector index to create.
    ///     Possible options are:
    ///         - vector-ivf
    ///         - vector-hnsw: available as a preview feature only,
    ///                        to enable visit https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/preview-features</param>
    /// <param name="numLists">This integer is the number of clusters that the inverted file (IVF) index uses to group the vector data.
    /// We recommend that numLists is set to documentCount/1000 for up to 1 million documents and to sqrt(documentCount)
    /// for more than 1 million documents. Using a numLists value of 1 is akin to performing brute-force search, which has
    /// limited performance.</param>
    /// <param name="similarity">Similarity metric to use with the IVF index.
    ///     Possible options are:
    ///         - COS (cosine distance),
    ///         - L2 (Euclidean distance), and
    ///         - IP (inner product).</param>
    /// <param name="dimensions">Number of dimensions for vector similarity. The maximum number of supported dimensions is 2000.</param>
    /// <param name="numberOfConnections">The max number of connections per layer (16 by default, minimum value is 2, maximum value is
    /// 100). Higher m is suitable for datasets with high dimensionality and/or high accuracy requirements.</param>
    /// <param name="efConstruction">The size of the dynamic candidate list for constructing the graph (64 by default, minimum value is 4,
    /// maximum value is 1000). Higher ef_construction will result in better index quality and higher accuracy, but it will
    /// also increase the time required to build the index. EfConstruction has to be at least 2 * m.</param>
    /// <param name="efSearch">The size of the dynamic candidate list for search (40 by default). A higher value provides better recall at
    /// the cost of speed.</param>
    public AzureCosmosDBMongoVCoreMemoryStore(
        string connectionString,
        string databaseName,
        string? indexName = "default_index",
        string? applicationName = "DotNet_Semantic_Kernel",
        string? kind = "vector_hnsw",
        int? numLists = 1,
        string? similarity = "COS",
        int? dimensions = 3,
        int? numberOfConnections = 16,
        int? efConstruction = 64,
        int? efSearch = 40
    )
    {
        MongoClientSettings settings = MongoClientSettings.FromConnectionString(connectionString);
        settings.ApplicationName = applicationName;
        this._cosmosDBMongoClient = new MongoClient(settings);
        this._cosmosMongoDatabase = this._cosmosDBMongoClient.GetDatabase(databaseName);
        this._indexName = indexName;
        this._kind = kind;
        this._numLists = (int)numLists;
        this._similarity = similarity;
        this._dimensions = (int)dimensions;
        this._numberOfConnections = (int)numberOfConnections;
        this._efConstruction = (int)efConstruction;
        this._efSearch = (int)efSearch;
    }

    public AzureCosmosDBMongoVCoreMemoryStore(
        IMongoClient mongoClient,
        string databaseName,
        string? indexName = "default_index",
        string? applicationName = "DotNet_Semantic_Kernel",
        string? kind = "vector_hnsw",
        int? numLists = 1,
        string? similarity = "COS",
        int? dimensions = 3,
        int? numberOfConnections = 16,
        int? efConstruction = 64,
        int? efSearch = 40
    )
    {
        MongoClientSettings settings = mongoClient.Settings;
        settings.ApplicationName = applicationName;
        this._cosmosDBMongoClient = new MongoClient(settings);
        this._cosmosMongoDatabase = this._cosmosDBMongoClient.GetDatabase(databaseName);
        this._indexName = indexName;
        this._kind = kind;
        this._numLists = (int)numLists;
        this._similarity = similarity;
        this._dimensions = (int)dimensions;
        this._numberOfConnections = (int)numberOfConnections;
        this._efConstruction = (int)efConstruction;
        this._efSearch = (int)efSearch;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(
        string collectionName,
        CancellationToken cancellationToken = default
    )
    {
        this._cosmosMongoDatabase.CreateCollectionAsync(
            collectionName,
            cancellationToken: cancellationToken
        );
        var indexes = await this.GetCollection(collectionName)
            .Indexes.ListAsync()
            .ConfigureAwait(false);

        if (!indexes.ToList().Any(index => index["name"] == this._indexName))
        {
            var command = new BsonDocument();
            switch (this._kind)
            {
                case "vector-ivf":
                    command = GetIndexDefinitionVectorIVF(collectionName);
                    break;
                case "vector-hnsw":
                    command = GetIndexDefinitionVectorHNSW(collectionName);
                    break;
            }
            await _cosmosMongoDatabase.RunCommandAsync<BsonDocument>(command).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync(
        [EnumeratorCancellation] CancellationToken cancellationToken = default
    )
    {
        using var cursor = await this
            ._cosmosMongoDatabase.ListCollectionNamesAsync(cancellationToken: cancellationToken)
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
        await foreach (var existingCollectionName in this.GetCollectionsAsync(cancellationToken))
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
    ) => this._cosmosMongoDatabase.DropCollectionAsync(collectionName, cancellationToken);

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(
        string collectionName,
        MemoryRecord record,
        CancellationToken cancellationToken = default
    )
    {
        var replaceOptions = new ReplaceOptions() { IsUpsert = true };

        var result = await GetCollection(collectionName)
            .ReplaceOneAsync(
                GetFilterById(record.Metadata.Id),
                new AzureCosmosDBMongoVCoreMemoryRecord(record),
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
        using var cursor = await this.VectorSearch(1, embedding, collectionName, cancellationToken)
            .ConfigureAwait(false);
        var result = await cursor.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
        // Access the similarityScore from the BSON document
        var similarityScore = result.GetValue("similarityScore").AsDouble;
        if (similarityScore < minRelevanceScore)
        {
            return null;
        }

        MemoryRecord memoryRecord = AzureCosmosDBMongoVCoreMemoryRecord.ToMemoryRecord(
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
        using var cursor = await this.VectorSearch(
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

                MemoryRecord memoryRecord = AzureCosmosDBMongoVCoreMemoryRecord.ToMemoryRecord(
                    doc["document"].AsBsonDocument,
                    withEmbeddings
                );
                yield return (memoryRecord, similarityScore);
            }
        }
    }

    /// <inheritdoc/>
    public async void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the resources used by the <see cref="MongoDBMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._cosmosDBMongoClient.Cluster.Dispose();
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
                        { "name", this._indexName },
                        {
                            "key",
                            new BsonDocument { { "embedding", "cosmosSearch" } }
                        },
                        {
                            "cosmosSearchOptions",
                            new BsonDocument
                            {
                                { "kind", this._kind },
                                { "numLists", this._numLists },
                                { "similarity", this._similarity },
                                { "dimensions", this._dimensions }
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
                        { "name", this._indexName },
                        {
                            "key",
                            new BsonDocument { { "embedding", "cosmosSearch" } }
                        },
                        {
                            "cosmosSearchOptions",
                            new BsonDocument
                            {
                                { "kind", this._kind },
                                { "m", this._numberOfConnections },
                                { "efConstruction", this._efConstruction },
                                { "similarity", this._similarity },
                                { "dimensions", this._dimensions }
                            }
                        }
                    }
                }
            }
        };
    }

    private async Task<IAsyncCursor<BsonDocument>> VectorSearch(
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

        BsonDocument[] pipeline = null;
        switch (this._kind)
        {
            case "vector-ivf":
                pipeline = GetVectorIVFSearchPipeline(embedding, limit);
                break;
            case "vector-hnsw":
                pipeline = GetVectorHNSWSearchPipeline(embedding, limit);
                break;
        }

        using var cursor = await this.GetCollection(collectionName)
            .AggregateAsync<BsonDocument>(pipeline)
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
            + string.Join(",", embedding.ToArray().Select(f => f.ToString()))
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
            @"
        {
            ""$project"": {
                ""similarityScore"": { ""$meta"": ""searchScore"" },
                ""document"": ""$$ROOT""
            }
        }";

        BsonDocument searchBson = BsonDocument.Parse(searchStage);
        BsonDocument projectBson = BsonDocument.Parse(projectStage);
        return new BsonDocument[] { searchBson, projectBson };
    }

    private BsonDocument[] GetVectorHNSWSearchPipeline(ReadOnlyMemory<float> embedding, int limit)
    {
        string searchStage =
            @"
        {
            ""$search"": {
                ""cosmosSearch"": {
                    ""vector"": ["
            + string.Join(",", embedding.ToArray().Select(f => f.ToString()))
            + @"],
                    ""path"": ""embedding"",
                    ""k"": "
            + limit
            + @",
                    ""efSearch"": "
            + this._efSearch
            + @"
                }
            }
        }";

        string projectStage =
            @"
        {
            ""$project"": {
                ""similarityScore"": { ""$meta"": ""searchScore"" },
                ""document"": ""$$ROOT""
            }
        }";

        BsonDocument searchBson = BsonDocument.Parse(searchStage);
        BsonDocument projectBson = BsonDocument.Parse(projectStage);
        return new BsonDocument[] { searchBson, projectBson };
    }

    private IMongoCollection<AzureCosmosDBMongoVCoreMemoryRecord> GetCollection(
        string collectionName
    ) =>
        this._cosmosMongoDatabase.GetCollection<AzureCosmosDBMongoVCoreMemoryRecord>(
            collectionName
        );

    private static FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord> GetFilterById(string id) =>
        Builders<AzureCosmosDBMongoVCoreMemoryRecord>.Filter.Eq(m => m.Id, id);

    private static FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord> GetFilterByIds(
        IEnumerable<string> ids
    ) => Builders<AzureCosmosDBMongoVCoreMemoryRecord>.Filter.In(m => m.Id, ids);
}
