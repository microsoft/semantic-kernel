// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Collections;
using Newtonsoft.Json;

namespace Microsoft.SemanticKernel.Connectors.Memory.Cosmos;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Azure Cosmos DB.
/// </summary>
/// <remarks>The Embedding data is saved to the Azure Cosmos DB database container specified in the constructor.
/// The embedding data persists between subsequent instances and has similarity search capability, handled by the client as Azure Cosmos DB is not a vector-native DB.
/// </remarks>
public class CosmosMemoryStore : IMemoryStore
{
    private Database _database;
    private string _databaseName;
    private ILogger _log;

    /// <summary>
    /// Constructor for a memory store backed by a Cosmos instance.
    /// </summary>
    /// <param name="client"></param>
    /// <param name="databaseName"></param>
    /// <param name="log"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    /// <exception cref="CosmosException"></exception>
    public async Task<CosmosMemoryStore> CreateAsync(CosmosClient client, string databaseName, ILogger? log = null, CancellationToken cancel = default)
    {
        this._databaseName = databaseName;
        this._log = log ?? NullLogger<CosmosMemoryStore>.Instance;
        var response = await client.CreateDatabaseIfNotExistsAsync(this._databaseName, cancellationToken: cancel);

        if (response.StatusCode == HttpStatusCode.Created)
        {
            this._log.LogInformation("Created database {0}", this._databaseName);
        }
        else if (response.StatusCode == HttpStatusCode.OK)
        {
            this._log.LogInformation("Database {0}", this._databaseName);
        }
        else
        {
            throw new CosmosException("Database does not exist and was not created", response.StatusCode, 0, this._databaseName, 0);
        }

        this._database = response.Database;

        return this;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        // Azure Cosmos DB does not support listing all Containers, this does not break the interface but it is not ideal.
        this._log.LogWarning("Listing all containers is not supported by Azure Cosmos DB, returning empty list.");

        return Enumerable.Empty<string>().ToAsyncEnumerable();
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        var properties = new ContainerProperties(collectionName, "/" + collectionName);
        var response = await this._database.CreateContainerIfNotExistsAsync(properties, cancellationToken: cancel);

        if (response.StatusCode == HttpStatusCode.Created)
        {
            this._log.LogInformation("Created collection {0}", collectionName);
        }
        else if (response.StatusCode == HttpStatusCode.OK)
        {
            this._log.LogInformation("Collection {0} already exists", collectionName);
        }
        else
        {
            throw new CosmosException("Collection does not exist and was not created", response.StatusCode, 0, collectionName, 0);
        }
    }

    /// <inheritdoc />
    public Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        return Task.FromResult(container != null);
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        var response = await container.DeleteContainerAsync(cancellationToken: cancel);

        if (response.StatusCode == HttpStatusCode.OK)
        {
            this._log.LogInformation("Collection {0} deleted", collectionName);
        }
        else
        {
            throw new CosmosException("Unable to delete collection", response.StatusCode, 0, collectionName, 0);
        }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);

        using (var responseMessage = await container.ReadItemStreamAsync(this.ToCosmosFriendlyId(key), new Microsoft.Azure.Cosmos.PartitionKey(collectionName), cancellationToken: cancel))
        {
            if (!responseMessage.IsSuccessStatusCode)
            {
                this._log?.LogWarning("Failed to get item {0} from collection {1} with status code {2}", key, collectionName, responseMessage.StatusCode);
                return null;
            }

            using (responseMessage.Content)
            {
                CosmosMemoryRecord record;

                if (typeof(Stream).IsAssignableFrom(typeof(CosmosMemoryRecord)))
                {
                    record = ((CosmosMemoryRecord)(object)responseMessage.Content);
                }
                else
                {
                    record = await System.Text.Json.JsonSerializer.DeserializeAsync<CosmosMemoryRecord>(responseMessage.Content, cancellationToken: cancel)
                        ?? throw new CosmosException($"Unable to deserialize content as CosmosMemoryRecord: {responseMessage.Content}.", responseMessage.StatusCode, 0, collectionName, 0);
                }

                var embeddingHost = JsonConvert.DeserializeAnonymousType(
                    record!.EmbeddingString,
                    new { Embedding = new { vector = new List<float>() } });

                return MemoryRecord.FromJson(
                    record.MetadataString,
                    new Embedding<float>(embeddingHost.Embedding.vector),
                    record.Id,
                    record.Timestamp);
            }
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var key in keys)
        {
            var record = await this.GetAsync(collectionName, key, cancel);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        record.Key = this.ToCosmosFriendlyId(record.Metadata.Id);

        var entity = new CosmosMemoryRecord
        {
            CollectionId = collectionName,
            Id = record.Key,
            Timestamp = record.Timestamp,
            EmbeddingString = string.Join(", ", record.Embedding.AsReadOnlySpan().ToArray()),
            MetadataString = record.GetSerializedMetadata()
        };

        var container = this._database.Client.GetContainer(this._databaseName, collectionName);

        await container.UpsertItemAsync(entity, cancellationToken: cancel, requestOptions: new ItemRequestOptions()
        {
            EnableContentResponseOnWrite = false,
        });

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var r in records)
        {
            yield return await this.UpsertAsync(collectionName, r, cancel);
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        var response = await container.DeleteItemAsync<CosmosMemoryRecord>(
            key,
            new Microsoft.Azure.Cosmos.PartitionKey(this.ToCosmosFriendlyId(key)),
            cancellationToken: cancel);

        if (response.StatusCode == HttpStatusCode.OK)
        {
            this._log.LogInformation("Record deleted from {0}", collectionName);
        }
        else
        {
            throw new CosmosException("Unable to delete record", response.StatusCode, 0, collectionName, 0);
        }
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        await Task.WhenAll(keys.Select(k => this.RemoveAsync(collectionName, k, cancel)));
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        {
            if (limit <= 0)
            {
                yield break;
            }

            var collectionMemories = new List<MemoryRecord>();
            TopNCollection<MemoryRecord> embeddings = new(limit);

            await foreach (var entry in this.GetAllAsync(collectionName, cancel))
            {
                if (entry != null)
                {
                    double similarity = embedding
                        .AsReadOnlySpan()
                        .CosineSimilarity(entry.Embedding.AsReadOnlySpan());
                    if (similarity >= minRelevanceScore)
                    {
                        embeddings.Add(new(entry, similarity));
                    }
                }
            }

            embeddings.SortByScore();

            foreach (var item in embeddings)
            {
                yield return (item.Value, item.Score.Value);
            }
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0,
        CancellationToken cancel = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            cancel: cancel).FirstOrDefaultAsync(cancellationToken: cancel);
    }

    /// <summary>
    /// Block constructor for a memory store backed by an Azure Cosmos DB instance. Not used.
    /// </summary>
    private CosmosMemoryStore(CosmosClient client, string databaseName, ILogger? log = null)
    {
        this._databaseName = databaseName;
        this._database = client.GetDatabase(this._databaseName);
        this._log = log ?? NullLogger<CosmosMemoryStore>.Instance;
    }

    private async IAsyncEnumerable<MemoryRecord> GetAllAsync(string collectionName, [EnumeratorCancellation] CancellationToken cancel = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        var query = new QueryDefinition($"SELECT * FROM c WHERE c.collectionId = @collectionName")
            .WithParameter("@collectionName", collectionName);

        var iterator = container.GetItemQueryIterator<CosmosMemoryRecord>(query);

        var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);

        foreach (var item in items)
        {
            var embeddingHost = JsonConvert.DeserializeAnonymousType(
                item.EmbeddingString,
                new { Embedding = new { vector = new List<float>() } });

            yield return MemoryRecord.FromJson(
                item.MetadataString,
                new Embedding<float>(embeddingHost.Embedding.vector),
                item.Id,
                item.Timestamp);
        }
    }

    private string ToCosmosFriendlyId(string id)
    {
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_').ToUpperInvariant()}";
    }
}
