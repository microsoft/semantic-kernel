// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Azure Cosmos DB database.
/// Get more details about Azure Cosmos DB vector search  https://learn.microsoft.com/en-us/azure/cosmos-db/
/// </summary>
public class AzureCosmosDBNoSQLMemoryStore : IMemoryStore, IDisposable
{
    private readonly CosmosClient _cosmosClient;
    private readonly Embedding _embedding;
    private readonly IndexingPolicy _indexingPolicy;

    /// <summary>
    /// Initiates a AzureCosmosDBNoSQLMemoryStore instance using a Azure Cosmos DB connection string
    /// and other properties required for vector search.
    /// </summary>
    /// <param name="connectionString">Connection string required to connect to Azure Cosmos DB.</param>
    /// <param name="databaseName">The database name to connect to.</param>
    /// <param name="config">Azure CosmosDB NoSQL Config containing specific parameters for vector search.</param>
    public AzureCosmosDBNoSQLMemoryStore(
        string connectionString,
        string databaseName,
        Embedding embedding,
        IndexingPolicy indexingPolicy,
        string applicationName,
    )
    {
        this._cosmosClient = new CosmosClient(connectionString);
        this._databaseName = databaseName;
    }

    /// <summary>
    /// Initiates a AzureCosmosDBNoSQLMemoryStore instance using a <see cref="CosmosClient"/> instance
    /// and other properties required for vector search.
    /// </summary>
    public AzureCosmosDBNoSQLMemoryStore(
        CosmosClient cosmosClient,
        string databaseName,
        AzureCosmosDBNoSQLonfig config)
    {
        MongoClientSettings settings = cosmosClient.Settings;
        this._config = config;
        settings.ApplicationName = this._config.ApplicationName;
        this._cosmosClient = new MongoClient(settings);
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
        var replaceOptions = new ReplaceOptions() { IsUpsert = true };

        var result = await this.GetCollection(collectionName)
            .ReplaceOneAsync(
                GetFilterById(record.Metadata.Id),
                new AzureCosmosDBNoSQLryRecord(record),
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

        MemoryRecord memoryRecord = AzureCosmosDBNoSQLmoryRecord.ToMemoryRecord(
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

                MemoryRecord memoryRecord = AzureCosmosDBNoSQLMemoryRecord.ToMemoryRecord(
                    doc["document"].AsBsonDocument,
                    withEmbeddings
                );
                yield return (memoryRecord, similarityScore);
            }
        }
    }

    /// <summary>
    /// Disposes the <see cref="AzureCosmosDBNoSQLMemoryStore"/> instance.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the resources used by the <see cref="AzureCosmosDBNoSQLMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._cosmosClient.Dispose();
        }
    }
}
