// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Collections;
using Microsoft.SemanticKernel.Memory.Storage;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json.Serialization;

namespace Skills.Memory.CosmosDB;
public class CosmosMemoryStore<TEmbedding> : IMemoryStore<TEmbedding>, IDisposable
    where TEmbedding : unmanaged
{
    private bool _disposedValue;

    private CosmosClient _client;
    private string _databaseName;
    private string _containerName;

    public CosmosMemoryStore(CosmosClient client, string databaseName, string containerName)
    {
        this._client = client;
        this._databaseName = databaseName;
        this._containerName = containerName;
    }

    public async Task<DataEntry<IEmbeddingWithMetadata<TEmbedding>>?> GetAsync(string collection, string key, CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);

        using (var responseMessage = await container.ReadItemStreamAsync(this._toCosmosFriendlyId(key), new Microsoft.Azure.Cosmos.PartitionKey(collection), cancellationToken: cancel))
        {
            if (responseMessage.IsSuccessStatusCode)
            {
                using (responseMessage.Content)
                {
                    CosmosMemoryRecord record;

                    if (typeof(Stream).IsAssignableFrom(typeof(CosmosMemoryRecord)))
                    {
                        record = ((CosmosMemoryRecord)(object)responseMessage.Content);
                    }
                    else
                    {
                        record = await System.Text.Json.JsonSerializer.DeserializeAsync<CosmosMemoryRecord>(responseMessage.Content!, cancellationToken: cancel);
                    }

                    var embeddingHost = JsonConvert.DeserializeAnonymousType(
                        record!.EmbeddingString,
                        new { Embedding = new { vector = new List<float>() } });

                    var rec = MemoryRecord.FromJson(
                        record.MetadataString,
                        new Embedding<float>(embeddingHost.Embedding.vector));

                    return DataEntry.Create<IEmbeddingWithMetadata<TEmbedding>>(
                                rec.Metadata.Id,
                                (IEmbeddingWithMetadata<TEmbedding>)rec,
                                record.Timestamp);
                }
            }
        }

        return null;
    }

    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);
        var query = new QueryDefinition($"SELECT DISTINCT c.collectionId FROM c");
        var iterator = container.GetItemQueryIterator<CosmosMemoryRecord>(query);

        var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);

        foreach (var item in items)
        {
            yield return item.CollectionId;
        }
    }

    public IAsyncEnumerable<(IEmbeddingWithMetadata<TEmbedding>, double)> GetNearestMatchesAsync(string collection, Embedding<TEmbedding> embedding, int limit = 1, double minRelevanceScore = 0)
    {
        if (limit <= 0)
        {
            return AsyncEnumerable.Empty<(IEmbeddingWithMetadata<TEmbedding>, double)>();
        }

        var asyncEmbeddingCollection = this.TryGetCollectionAsync(collection);
        var embeddingCollection = asyncEmbeddingCollection.ToEnumerable().ToArray();

        if (embeddingCollection == null || !embeddingCollection.Any())
        {
            return AsyncEnumerable.Empty<(IEmbeddingWithMetadata<TEmbedding>, double)>();
        }

        EmbeddingReadOnlySpan<TEmbedding> embeddingSpan = new(embedding.AsReadOnlySpan());

        TopNCollection<IEmbeddingWithMetadata<TEmbedding>> embeddings = new(limit);

        foreach (var item in embeddingCollection)
        {
            if (item.Value != null)
            {
                EmbeddingReadOnlySpan<TEmbedding> itemSpan = new(item.Value.Embedding.AsReadOnlySpan());
                double similarity = embeddingSpan.CosineSimilarity(itemSpan);
                if (similarity >= minRelevanceScore)
                {
                    embeddings.Add(new(item.Value, similarity));
                }
            }
        }

        embeddings.SortByScore();

        return embeddings.Select(x => (x.Value, x.Score.Value)).ToAsyncEnumerable();
    }

    protected async IAsyncEnumerable<DataEntry<IEmbeddingWithMetadata<TEmbedding>>> TryGetCollectionAsync(string collectionName, [EnumeratorCancellation] CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);
        var query = new QueryDefinition($"SELECT * FROM c WHERE c.collectionId = '{collectionName}'");
        var iterator = container.GetItemQueryIterator<CosmosMemoryRecord>(query);

        var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);

        foreach (var item in items)
        {
            var embeddingHost = JsonConvert.DeserializeAnonymousType(
                item.EmbeddingString,
                new { Embedding = new { vector = new List<float>() } });

            var rec = MemoryRecord.FromJson(
                item.MetadataString,
                new Embedding<float>(embeddingHost.Embedding.vector));

            yield return DataEntry.Create<IEmbeddingWithMetadata<TEmbedding>>(
                rec.Metadata.Id,
                (IEmbeddingWithMetadata<TEmbedding>)rec,
                item.Timestamp);
        }
    }

    public async Task<DataEntry<IEmbeddingWithMetadata<TEmbedding>>> PutAsync(string collection, DataEntry<IEmbeddingWithMetadata<TEmbedding>> data, CancellationToken cancel = default)
    {
        var entity = new CosmosMemoryRecord
        {
            CollectionId = collection,
            Id = this._toCosmosFriendlyId(data.Key),
            Timestamp = data.Timestamp,
            EmbeddingString = data.ValueString!,
            MetadataString = data.Value!.GetSerializedMetadata()
        };

        var container = this._client.GetContainer(this._databaseName, this._containerName);

        try
        {
            await container.CreateItemAsync(entity, cancellationToken: cancel, requestOptions: new ItemRequestOptions()
            {
                EnableContentResponseOnWrite = false
            });
        }
        catch (CosmosException ex)
        {
            if (ex.StatusCode == System.Net.HttpStatusCode.Conflict)
            {
                //TODO: log/handle
            }
        }


        return data;
    }

    public Task RemoveAsync(string collection, string key, CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);

        return container.DeleteItemAsync<CosmosMemoryRecord>(
            this._toCosmosFriendlyId(key),
            new Microsoft.Azure.Cosmos.PartitionKey(collection),
            cancellationToken: cancel);
    }

    private string _toCosmosFriendlyId(string id)
    {
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_').ToUpperInvariant()}";
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                // TODO: dispose managed state (managed objects)
                this._client.Dispose();
            }

            // TODO: free unmanaged resources (unmanaged objects) and override finalizer
            // TODO: set large fields to null
            this._disposedValue = true;
        }
    }

    // // TODO: override finalizer only if 'Dispose(bool disposing)' has code to free unmanaged resources
    // ~CosmosMemoryStore()
    // {
    //     // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
    //     Dispose(disposing: false);
    // }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}

[JsonObject(NamingStrategyType = typeof(CamelCaseNamingStrategy))]
public class CosmosMemoryRecord : IEmbeddingWithMetadata<float>
{
    public string Id { get; set; } = string.Empty;

    public string CollectionId { get; set; } = string.Empty;

    public DateTimeOffset? Timestamp { get; set; }

    [JsonIgnore]
    public Embedding<float> Embedding { get; set; } = new();

    public string EmbeddingString { get; set; } = string.Empty;

    /// <summary>
    /// Metadata associated with a Semantic Kernel memory.
    /// </summary>
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
    [JsonIgnore]
    public MemoryRecordMetadata Metadata { get; set; }
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

    public string MetadataString { get; set; } = string.Empty;

    public string GetSerializedMetadata()
    {
        return JsonConvert.SerializeObject(this.Metadata);
    }
}
