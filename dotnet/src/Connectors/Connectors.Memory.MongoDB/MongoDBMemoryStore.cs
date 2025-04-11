// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;
using MongoDB.Driver.Core.Configuration;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a MongoDB database.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and MongoDBVectorStore")]
public class MongoDBMemoryStore : IMemoryStore, IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBMemoryStore"/> class.
    /// </summary>
    /// <param name="connectionString">MongoDB connection string.</param>
    /// <param name="databaseName">Database name.</param>
    /// <param name="indexName">Name of the search index. If no value is provided default index will be used.</param>
    public MongoDBMemoryStore(string connectionString, string databaseName, string? indexName = default) :
        this(new MongoClient(GetMongoClientSettings(connectionString)), databaseName, indexName)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBMemoryStore" /> class.
    /// </summary>
    /// <param name="mongoClient">MongoDB client.</param>
    /// <param name="databaseName">Database name.</param>
    /// <param name="indexName">Name of the search index. If no value is provided default index will be used.</param>
    public MongoDBMemoryStore(IMongoClient mongoClient, string databaseName, string? indexName = default)
    {
        this._indexName = indexName;
        this._mongoClient = mongoClient;
        this._mongoDatabase = this._mongoClient.GetDatabase(databaseName);
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default) =>
       this._mongoDatabase.CreateCollectionAsync(collectionName, cancellationToken: cancellationToken);

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var cursor = await this._mongoDatabase.ListCollectionNamesAsync(cancellationToken: cancellationToken).ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var name in cursor.Current)
            {
                yield return name;
            }
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await foreach (var existingCollectionName in this.GetCollectionsAsync(cancellationToken).ConfigureAwait(false))
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
        record.Key = record.Metadata.Id;
        var filter = Builders<MongoDBMemoryEntry>.Filter.Eq(m => m.Id, record.Key);

        var replaceOptions = new ReplaceOptions() { IsUpsert = true };

        var result = await this._mongoDatabase.GetCollection<MongoDBMemoryEntry>(collectionName)
            .ReplaceOneAsync(filter, new MongoDBMemoryEntry(record), replaceOptions, cancellationToken)
            .ConfigureAwait(false);

        return result.UpsertedId?.AsString ?? record.Key;
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
        using var cursor = await this.Find(
            collectionName,
            GetFilterById(key),
            withEmbedding,
            cancellationToken)
            .ConfigureAwait(false);

        var mongoDBMemoryEntry = await cursor.SingleOrDefaultAsync(cancellationToken).ConfigureAwait(false);
        var result = mongoDBMemoryEntry?.ToMemoryRecord();

        return result;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var cursor = await this.Find(
            collectionName,
            GetFilterByIds(keys),
            withEmbeddings,
            cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var memoryRecord in cursor.Current)
            {
                yield return memoryRecord.ToMemoryRecord();
            }
        }
    }

    /// <inheritdoc/>
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default) =>
        this.GetCollection(collectionName).DeleteOneAsync(GetFilterById(key), cancellationToken);

    /// <inheritdoc/>
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default) =>
         this.GetCollection(collectionName).DeleteManyAsync(GetFilterByIds(keys), cancellationToken);

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var cursor = await this.VectorSearch(collectionName, embedding, limit, minRelevanceScore, withEmbeddings, cancellationToken).ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var memoryEntry in cursor.Current)
            {
                yield return memoryEntry.ToMemoryRecordAndScore();
            }
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        using var cursor = await this.VectorSearch(collectionName, embedding, 1, minRelevanceScore, withEmbedding, cancellationToken).ConfigureAwait(false);

        var result = await cursor.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);

        return result?.ToMemoryRecordAndScore();
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    /// <summary>
    /// Disposes the resources used by the <see cref="MongoDBMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._mongoClient.Cluster.Dispose();
        }
    }

    #endregion

    #region private ================================================================================

    private readonly string? _indexName;
    private readonly IMongoClient _mongoClient;
    private readonly IMongoDatabase _mongoDatabase;

    private IMongoCollection<MongoDBMemoryEntry> GetCollection(string collectionName) =>
        this._mongoDatabase.GetCollection<MongoDBMemoryEntry>(collectionName);

    private Task<IAsyncCursor<MongoDBMemoryEntry>> Find(
       string collectionName,
       FilterDefinition<MongoDBMemoryEntry> filter,
       bool withEmbeddings = false,
       CancellationToken cancellationToken = default)
    {
        var collection = this._mongoDatabase.GetCollection<MongoDBMemoryEntry>(collectionName);
        var findOptions = withEmbeddings ? null : new FindOptions<MongoDBMemoryEntry>() { Projection = Builders<MongoDBMemoryEntry>.Projection.Exclude(e => e.Embedding) };

        return collection.FindAsync(filter, findOptions, cancellationToken);
    }

    private static FilterDefinition<MongoDBMemoryEntry> GetFilterById(string id) =>
        Builders<MongoDBMemoryEntry>.Filter.Eq(m => m.Id, id);

    private static FilterDefinition<MongoDBMemoryEntry> GetFilterByIds(IEnumerable<string> ids) =>
        Builders<MongoDBMemoryEntry>.Filter.In(m => m.Id, ids);

    private static MongoClientSettings GetMongoClientSettings(string connectionString)
    {
        var settings = MongoClientSettings.FromConnectionString(connectionString);
        var skVersion = typeof(IMemoryStore).Assembly.GetName().Version?.ToString();
        settings.LibraryInfo = new LibraryInfo("Microsoft Semantic Kernel", skVersion);
        return settings;
    }

    private Task<IAsyncCursor<MongoDBMemoryEntry>> VectorSearch(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit = 1,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        var projectionDefinition = Builders<MongoDBMemoryEntry>
            .Projection
            .Meta(nameof(MongoDBMemoryEntry.Score), "vectorSearchScore")
            .Include(e => e.Metadata)
            .Include(e => e.Timestamp);

        if (withEmbedding)
        {
            projectionDefinition = projectionDefinition.Include(e => e.Embedding);
        }

        var vectorSearchOptions = new VectorSearchOptions<MongoDBMemoryEntry>() { IndexName = this._indexName };
        var aggregationPipeline = this.GetCollection(collectionName)
            .Aggregate()
            .VectorSearch(e => e.Embedding, embedding, limit, vectorSearchOptions)
            .Project<MongoDBMemoryEntry>(projectionDefinition);

        if (minRelevanceScore > 0)
        {
            aggregationPipeline = aggregationPipeline.Match(Builders<MongoDBMemoryEntry>.Filter.Gte(m => m.Score, minRelevanceScore));
        }

        return aggregationPipeline.ToCursorAsync(cancellationToken);
    }

    #endregion
}
