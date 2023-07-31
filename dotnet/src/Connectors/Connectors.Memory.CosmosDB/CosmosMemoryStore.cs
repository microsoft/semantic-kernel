// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCosmosDb;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Azure Cosmos DB.
/// </summary>
/// <remarks>The Embedding data is saved to the Azure Cosmos DB database container specified in the constructor.
/// The embedding data persists between subsequent instances and has similarity search capability, handled by the client as Azure Cosmos DB is not a vector-native DB.
/// </remarks>
public sealed class CosmosMemoryStore : IMemoryStore
{
    private Database _database;
    private string _databaseName;
    private ILogger _logger;

#pragma warning disable CS8618 // Non-nullable field is uninitialized: Class instance is created and populated via factory method.
    private CosmosMemoryStore()
    {
    }
#pragma warning restore CS8618 // Non-nullable field is uninitialized

    /// <summary>
    /// Factory method to initialize a new instance of the <see cref="CosmosMemoryStore"/> class.
    /// </summary>
    /// <param name="client">Client with endpoint and authentication to the Azure CosmosDB Account.</param>
    /// <param name="databaseName">The name of the database to back the memory store.</param>
    /// <param name="logger">Optional logger.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <exception cref="CosmosException"></exception>
    public static async Task<CosmosMemoryStore> CreateAsync(CosmosClient client, string databaseName, ILogger? logger = null, CancellationToken cancellationToken = default)
    {
        var newStore = new CosmosMemoryStore();

        newStore._databaseName = databaseName;
        newStore._logger = logger ?? NullLogger<CosmosMemoryStore>.Instance;
        var response = await client.CreateDatabaseIfNotExistsAsync(newStore._databaseName, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.Created)
        {
            newStore._logger.LogDebug("Created database {0}", newStore._databaseName);
        }
        else if (response.StatusCode == HttpStatusCode.OK)
        {
            newStore._logger.LogDebug("Database {0}", newStore._databaseName);
        }
        else
        {
            throw new CosmosException("Database does not exist and was not created", response.StatusCode, 0, newStore._databaseName, 0);
        }

        newStore._database = response.Database;

        return newStore;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        // Azure Cosmos DB does not support listing all Containers, this does not break the interface but it is not ideal.
        this._logger.LogWarning("Listing all containers is not supported by Azure Cosmos DB, returning empty list.");

        return Enumerable.Empty<string>().ToAsyncEnumerable();
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var response = await this._database.CreateContainerIfNotExistsAsync(collectionName, "/" + collectionName, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.Created)
        {
            this._logger.LogDebug("Created collection {0}", collectionName);
        }
        else if (response.StatusCode == HttpStatusCode.OK)
        {
            this._logger.LogDebug("Collection {0} already exists", collectionName);
        }
        else
        {
            throw new CosmosException("Collection does not exist and was not created", response.StatusCode, 0, collectionName, 0);
        }
    }

    /// <inheritdoc />
    public Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        // Azure Cosmos DB does not support checking if container exists without attempting to create it.
        // Note that CreateCollectionIfNotExistsAsync() is idempotent. This does not break the interface but it is not ideal.
        return Task.FromResult(false);
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        try
        {
            await container.DeleteContainerAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (CosmosException ex)
        {
            this._logger.LogError(ex, "Failed to delete collection {0}: {2} - {3}", collectionName, ex.StatusCode, ex.Message);
        }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var id = this.ToCosmosFriendlyId(key);
        var partitionKey = PartitionKey.None;

        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        MemoryRecord? memoryRecord = null;

        var response = await container.ReadItemAsync<CosmosMemoryRecord>(id, partitionKey, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response == null)
        {
            this._logger?.LogWarning("Received no get response collection {1}", collectionName);
        }
        else if (response.StatusCode != HttpStatusCode.OK)
        {
            this._logger?.LogWarning("Failed to get record from collection {1} with status code {2}", collectionName, response.StatusCode);
        }
        else
        {
            var result = response.Resource;

            float[]? vector = withEmbedding ? System.Text.Json.JsonSerializer.Deserialize<float[]>(result.EmbeddingString) : System.Array.Empty<float>();

            if (vector != null)
            {
                memoryRecord = MemoryRecord.FromJsonMetadata(
                    result.MetadataString,
                    new Embedding<float>(vector, transferOwnership: true),
                    result.Id,
                    result.Timestamp);
            }
        }

        return memoryRecord;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var record = await this.GetAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        record.Key = this.ToCosmosFriendlyId(record.Metadata.Id);

        var entity = new CosmosMemoryRecord
        {
            CollectionId = this.ToCosmosFriendlyId(collectionName),
            Id = record.Key,
            Timestamp = record.Timestamp,
            EmbeddingString = System.Text.Json.JsonSerializer.Serialize(record.Embedding.Vector),
            MetadataString = record.GetSerializedMetadata()
        };

        var container = this._database.Client.GetContainer(this._databaseName, collectionName);

        var response = await container.UpsertItemAsync(entity, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response.StatusCode is HttpStatusCode.OK or HttpStatusCode.Created)
        {
            this._logger.LogDebug("Upserted item to collection {0}", collectionName);
        }
        else
        {
            throw new CosmosException("Unable to upsert item collection", response.StatusCode, 0, collectionName, 0);
        }

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var r in records)
        {
            yield return await this.UpsertAsync(collectionName, r, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        var response = await container.DeleteItemAsync<CosmosMemoryRecord>(
            key,
            PartitionKey.None,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.OK)
        {
            this._logger.LogDebug("Record deleted from {0}", collectionName);
        }
        else
        {
            throw new CosmosException("Unable to delete record", response.StatusCode, 0, collectionName, 0);
        }
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(keys.Select(k => this.RemoveAsync(collectionName, k, cancellationToken))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        {
            if (limit <= 0)
            {
                yield break;
            }

            var collectionMemories = new List<MemoryRecord>();
            TopNCollection<MemoryRecord> embeddings = new(limit);

            await foreach (var record in this.GetAllAsync(collectionName, cancellationToken))
            {
                if (record != null)
                {
                    double similarity = embedding
                        .AsReadOnlySpan()
                        .CosineSimilarity(record.Embedding.AsReadOnlySpan());
                    if (similarity >= minRelevanceScore)
                    {
                        var entry = withEmbeddings ? record : MemoryRecord.FromMetadata(record.Metadata, Embedding<float>.Empty, record.Key, record.Timestamp);
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
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbedding,
            cancellationToken: cancellationToken).FirstOrDefaultAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<MemoryRecord> GetAllAsync(string collectionName, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        var query = new QueryDefinition("SELECT * FROM c");

        var iterator = container.GetItemQueryIterator<CosmosMemoryRecord>(query);

        while (iterator.HasMoreResults) //read all result in batch
        {
            var items = await iterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

            foreach (var item in items)
            {
                var vector = System.Text.Json.JsonSerializer.Deserialize<float[]>(item.EmbeddingString);

                if (vector != null)
                {
                    yield return MemoryRecord.FromJsonMetadata(
                        item.MetadataString,
                        new Embedding<float>(vector, transferOwnership: true),
                        item.Id,
                        item.Timestamp);
                }
            }
        }
    }

    private string ToCosmosFriendlyId(string id)
    {
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_').ToUpperInvariant()}";
    }
}
