// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Azure.Cosmos.Scripts;
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
    private ILogger _log;
    private readonly string _queryWithEmbedding = "select * from (SELECT c.id,c.collectionId,c.timestamp,c.embeddingString,c.metadataString,udf.CosinSimularity(@embedding,c.embeddingString) as score FROM c) cc where cc.score>@minScore";
    private readonly string _queryWithoutEmbedding = "select * from (SELECT c.id,c.collectionId,c.timestamp,c.metadataString,udf.CosinSimularity(@embedding,c.embeddingString) as score FROM c) cc where cc.score>@minScore";
    private SortedSet<string> _collectionCache = null;
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
    /// <param name="log">Optional logger.</param>
    /// <param name="cancel">Optional cancellation token.</param>
    /// <exception cref="CosmosException"></exception>
    public static async Task<CosmosMemoryStore> CreateAsync(CosmosClient client, string databaseName, ILogger? log = null, CancellationToken cancel = default)
    {
        var newStore = new CosmosMemoryStore();

        newStore._databaseName = databaseName;
        newStore._log = log ?? NullLogger<CosmosMemoryStore>.Instance;
        var response = await client.CreateDatabaseIfNotExistsAsync(newStore._databaseName, cancellationToken: cancel).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.Created)
        {
            newStore._log.LogInformation("Created database {0}", newStore._databaseName);
        }
        else if (response.StatusCode == HttpStatusCode.OK)
        {
            newStore._log.LogInformation("Database {0}", newStore._databaseName);
        }
        else
        {
            throw new CosmosException("Database does not exist and was not created", response.StatusCode, 0, newStore._databaseName, 0);
        }

        newStore._database = response.Database;
        await newStore.RefreshCollectionCacheAsync(cancel).ConfigureAwait(false);
        return newStore;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var item in this._collectionCache)
        {
            yield return item;
        }
    }


    /// <inheritdoc />
    private async Task RefreshCollectionCacheAsync(CancellationToken cancel = default)
    {
        this._collectionCache = new SortedSet<string>();
        QueryDefinition queryDefinition = new QueryDefinition("select * from c");
        var iterator = this._database.GetContainerQueryIterator<ContainerProperties>(queryDefinition);
        while (iterator.HasMoreResults)
        {
            foreach (var item in await iterator.ReadNextAsync(cancel).ConfigureAwait(false))
            {
                this._collectionCache.Add(item.Id);
            }
        }
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {

        ContainerProperties newContainer = new ContainerProperties(collectionName, "/" + collectionName);
        newContainer.IndexingPolicy = new IndexingPolicy()
        {
            Automatic = true,
            IndexingMode = IndexingMode.Consistent,//id and _ts will automatically indexed
            ExcludedPaths = { new ExcludedPath() { Path = "/embeddingString/?" } },
            IncludedPaths = { new IncludedPath() { Path = "/*" } }
        };
        newContainer.PartitionKeyPath = "/id";
        var response = await this._database.CreateContainerIfNotExistsAsync(newContainer, cancellationToken: cancel).ConfigureAwait(false);
        if (response.StatusCode == HttpStatusCode.Created)
        {
            this._log.LogInformation("Created collection {0}", collectionName);
            //change indexing policy
            response.Resource.IndexingPolicy = new IndexingPolicy();


            //create UDF
            var createFunctionResponse = await response.Container.Scripts.CreateUserDefinedFunctionAsync(new UserDefinedFunctionProperties() { Id = "CosinSimularity", Body = ScriptResources.UDF_CosinSimularity }, cancellationToken: cancel).ConfigureAwait(false);
            if (createFunctionResponse.StatusCode == HttpStatusCode.Created)
            {
                this._log.LogInformation("Created UDF CosinSimularity in collection {0}", collectionName);
                this._collectionCache.Add(collectionName);
            }
            else
            {
                throw new CosmosException($"Failed create UDF CosinSimularity in collection {collectionName}", createFunctionResponse.StatusCode, 0, collectionName, 0);
            }

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
        return Task.FromResult(this._collectionCache.Contains(collectionName));

    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        try
        {
            await container.DeleteContainerAsync(cancellationToken: cancel).ConfigureAwait(false);
            this._collectionCache.Remove(collectionName);
        }
        catch (CosmosException ex)
        {
            this._log.LogError(ex, "Failed to delete collection {0}: {2} - {3}", collectionName, ex.StatusCode, ex.Message);
        }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancel = default)
    {
        var id = this.ToCosmosFriendlyId(key);
        var partitionKey = new PartitionKey(key);
        if (!this._collectionCache.Contains(collectionName))
        {
            return null;
        }
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        MemoryRecord? memoryRecord = null;
        try
        {
            var response = await container.ReadItemAsync<CosmosMemoryRecord>(id, partitionKey, cancellationToken: cancel).ConfigureAwait(false);
            if (response == null)
            {
                this._log?.LogWarning("Received no get response collection {1}", collectionName);
            }
            else if (response.StatusCode != HttpStatusCode.OK)
            {
                this._log?.LogWarning("Failed to get record from collection {1} with status code {2}", collectionName, response.StatusCode);
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
        catch (CosmosException ce)
        {
            if (ce.StatusCode == HttpStatusCode.NotFound)
            {
                this._log?.LogWarning("record not found in collection", collectionName);
                return null;
            }
            else
            {
                throw;
            }

        }

    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._collectionCache.Contains(collectionName))
        {
            yield break;
        }
        foreach (var key in keys)
        {
            var record = await this.GetAsync(collectionName, key, withEmbeddings, cancel).ConfigureAwait(false);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        if (!this._collectionCache.Contains(collectionName))
        {
            await this.CreateCollectionAsync(collectionName, cancel).ConfigureAwait(false);
        }
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

        var response = await container.UpsertItemAsync(entity, cancellationToken: cancel).ConfigureAwait(false);

        if (response.StatusCode is HttpStatusCode.OK or HttpStatusCode.Created)
        {
            this._log.LogInformation("Upserted item to collection {0}", collectionName);
        }
        else
        {
            throw new CosmosException("Unable to upsert item collection", response.StatusCode, 0, collectionName, 0);
        }

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var r in records)
        {
            yield return await this.UpsertAsync(collectionName, r, cancel).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        if (!this._collectionCache.Contains(collectionName))
        {
            return;
        }
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        ItemResponse<CosmosMemoryRecord> response = null;
        try
        {
            response = await container.DeleteItemAsync<CosmosMemoryRecord>(key, new PartitionKey(key), cancellationToken: cancel).ConfigureAwait(false);
        }
        catch (CosmosException ce)
        {
            if (ce.StatusCode == HttpStatusCode.NotFound)//ignore if no item is found
            {
                this._log.LogInformation("Record not found from {0}", collectionName);
                return;
            }
            else
            {
                throw;
            }

        }
        if (response.StatusCode == HttpStatusCode.NoContent)
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
        if (!this._collectionCache.Contains(collectionName))
        {
            return;
        }
        await Task.WhenAll(keys.Select(k => this.RemoveAsync(collectionName, k, cancel))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        {
            if (limit <= 0 || !this._collectionCache.Contains(collectionName))
            {
                yield break;
            }

            var collectionMemories = new List<MemoryRecord>();
            TopNCollection<MemoryRecord> embeddings = new(limit);
            string embeddingParameter = JsonSerializer.Serialize(embedding.Vector);
            var container = this._database.Client.GetContainer(this._databaseName, collectionName);



            QueryDefinition query =
                new QueryDefinition(withEmbeddings ? this._queryWithEmbedding : this._queryWithoutEmbedding)
                .WithParameter("@embedding", embeddingParameter)
                .WithParameter("@minScore", minRelevanceScore);
            var iterator = container.GetItemQueryIterator<CosmosMemoryRecordWithScore>(query);


            while (iterator.HasMoreResults)
            {
                var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);
                foreach (var item in items)
                {
                    Embedding<float>? embeddingObject = null;
                    if (withEmbeddings)
                    {
                        float[] embeddingValue = JsonSerializer.Deserialize<float[]>(item.EmbeddingString);
                        embeddingObject = new Embedding<float>(embeddingValue);
                    }

                    var record = MemoryRecord.FromJsonMetadata(
                    item.MetadataString,
                        embeddingObject,
                        item.Id,
                        item.Timestamp);
                    embeddings.Add(record, item.Score);
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
        CancellationToken cancel = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbedding,
            cancel: cancel).FirstOrDefaultAsync(cancellationToken: cancel).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<MemoryRecord> GetAllAsync(string collectionName, [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._collectionCache.Contains(collectionName))
        {
            yield break;
        }
        var container = this._database.Client.GetContainer(this._databaseName, collectionName);
        var query = new QueryDefinition("SELECT * FROM c");

        var iterator = container.GetItemQueryIterator<CosmosMemoryRecord>(query);

        while (iterator.HasMoreResults) //read all result in batch

        {
            var items = await iterator.ReadNextAsync(cancel).ConfigureAwait(false);

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
        return $"{id.Trim().Replace(' ', '-').Replace('/', '_').Replace('\\', '_').Replace('?', '_').Replace('#', '_')}";
    }
}
