// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;

namespace Skills.Memory.CosmosDB;
public class CosmosDataStore<TValue> : IDataStore<TValue>, IDisposable
{
    private bool _disposedValue;

    private CosmosClient _client;
    private string _databaseName;
    private string _containerName;

    public CosmosDataStore(CosmosClient client, string databaseName, string containerName)
    {
        this._client = client;
        this._databaseName = databaseName;
        this._containerName = containerName;
    }

    public async IAsyncEnumerable<DataEntry<TValue>> GetAllAsync(string collection, CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);
        var query = new QueryDefinition($"SELECT * FROM c WHERE c.collectionId = '{collection}'");
        var iterator = container.GetItemQueryIterator<DataEntry<TValue>>(query);

        var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);

        foreach (var item in items)
        {
            yield return item;
        }
    }

    public async Task<DataEntry<TValue>?> GetAsync(string collection, string key, CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);

        using (var responseMessage = await container.ReadItemStreamAsync(this._toCosmosFriendlyId(key), new Microsoft.Azure.Cosmos.PartitionKey(collection), cancellationToken: cancel))
        {
            if (responseMessage.IsSuccessStatusCode)
            {
                using (responseMessage.Content)
                {
                    CosmosProxyModel<TValue> proxy;

                    if (typeof(Stream).IsAssignableFrom(typeof(CosmosProxyModel<TValue>)))
                    {
                        proxy = ((CosmosProxyModel<TValue>)(object)responseMessage.Content);
                    }
                    else
                    {
                        proxy = await System.Text.Json.JsonSerializer.DeserializeAsync<CosmosProxyModel<TValue>>(responseMessage.Content, cancellationToken: cancel);
                    }

                    return DataEntry.Create<TValue>(proxy.Id, proxy.ValueString, proxy.Timestamp);
                }
            }
        }

        return default(DataEntry<TValue>);
    }

    public async IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);
        var query = new QueryDefinition($"SELECT DISTINCT c.collectionId FROM c");
        var iterator = container.GetItemQueryIterator<CosmosProxyModel<TValue>>(query);

        var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);

        foreach (var item in items)
        {
            yield return item.CollectionId;
        }
    }

    public async Task<DataEntry<TValue>> PutAsync(string collection, DataEntry<TValue> data, CancellationToken cancel = default)
    {
        var entity = new CosmosProxyModel<TValue>()
        {
            CollectionId = collection,
            Id = this._toCosmosFriendlyId(data.Key),
            Timestamp = data.Timestamp,
            ValueString = data.ValueString
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

        return container.DeleteItemAsync<CosmosProxyModel<TValue>>(this._toCosmosFriendlyId(key), new Microsoft.Azure.Cosmos.PartitionKey(collection), cancellationToken: cancel);
    }

    protected async IAsyncEnumerable<DataEntry<TValue>> TryGetCollectionAsync(string name)
    {
        var container = this._client.GetContainer(this._databaseName, this._containerName);
        var query = new QueryDefinition($"SELECT * FROM c WHERE c.collectionId = '{name}'");
        var iterator = container.GetItemQueryIterator<CosmosProxyModel<TValue>>(query);

        var items = await iterator.ReadNextAsync().ConfigureAwait(false);

        foreach (var item in items)
        {
            //TODO: fix temporary hardcode and pass the correct value below
            var value = System.Text.Json.JsonSerializer.Deserialize<SimpleEmbedding<float>>(item.ValueString);

            yield return new DataEntry<TValue>(
                item.Id,
                default(TValue),
                item.Timestamp);
        }
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

    private string _toCosmosFriendlyId(string id)
    {
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_').ToUpperInvariant()}";
    }
}

[JsonObject(NamingStrategyType = typeof(CamelCaseNamingStrategy))]
public class CosmosProxyModel<TValue>
{
    public string CollectionId { get; set; } = string.Empty;

    public string Id { get; set; } = string.Empty;

    public DateTimeOffset? Timestamp { get; set; }

    public string ValueString { get; set; } = string.Empty;
}

public class SimpleEmbedding<TValue> : IEmbeddingWithMetadata<TValue> where TValue : unmanaged
{
    public Embedding<TValue> Embedding { get; set; } = new();
}
