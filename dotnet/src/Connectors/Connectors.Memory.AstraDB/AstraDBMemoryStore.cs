using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;


namespace Microsoft.SemanticKernel.Connectors.AstraDB;

public class AstraDBMemoryStore : IMemoryStore
{
  /// <summary>
  /// Initializes a new instance of the <see cref="AstraDBMemoryStore"/> class.
  /// </summary>
  /// <param name="apiEndpoint">Astra DB API endpoint.</param>
  /// <param name="appToken">Application token for Astra DB.</param>
  /// <param name="keySpace">Name of the keyspace to work with.</param>
  /// <param name="vectorSize">Embedding vector size.</param>
  public AstraDBMemoryStore(string apiEndpoint, string appToken, string keySpace = "default_keyspaces", int vectorSize = 1536)
  {
    this._astraDbClient = new AstraDBClient(apiEndpoint, appToken, keySpace, vectorSize);
  }

  /// <inheritdoc/>
  public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
  {
    await this._astraDbClient.CreateCollectionAsync(collectionName).ConfigureAwait(false);
  }

  /// <inheritdoc/>
  public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
  {
    await foreach (var name in this._astraDbClient.GetCollectionsAsync(cancellationToken).ConfigureAwait(false))
    {
      yield return name;
    }
  }

  public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
  {
    await foreach (var dbcollectionName in this.GetCollectionsAsync(cancellationToken).ConfigureAwait(false))
    {
      if (dbcollectionName == collectionName)
      {
        return true;
      }
    }

    return false;
  }

  /// <inheritdoc/>
  public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default) =>
    await this._astraDbClient.DeleteCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);

  /// <inheritdoc/>
  public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
  {
    record.Key = record.Metadata.Id;
    float[]? embeddingArray = record.Embedding.ToArray();

    await this._astraDbClient.UpsertAsync(
      collectionName,
      key: record.Key,
      metadata: record.GetSerializedMetadata(),
      embedding: embeddingArray,
      cancellationToken: cancellationToken).ConfigureAwait(false);

    return record.Key;
  }

  /// <inheritdoc/>
  public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
  {
    foreach (MemoryRecord record in records)
    {
      yield return await this.UpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
    }
  }

  /// <inheritdoc/>
  public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
  {
    if (await DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
    {
      return await this._astraDbClient.FindOneAsync(collectionName, key, withEmbedding = false, cancellationToken).ConfigureAwait(false);
    }

    return null;
  }

  /// <inheritdoc/>
  public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
    string collectionName,
    IEnumerable<string> keys,
    bool withEmbeddings = false,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
  {
    if (!await DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
    {
      yield break;
    }

    foreach (var key in keys)
    {
      var record = await this._astraDbClient.FindOneAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
      if (record != null)
      {
        yield return record;
      }
    }
  }

  /// <inheritdoc/>
  public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
  {
    await this._astraDbClient.DeleteOneAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
  }

  /// <inheritdoc/>
  public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
  {
    await this._astraDbClient.DeleteManyAsync(collectionName, keys, cancellationToken).ConfigureAwait(false);
  }


  /// <inheritdoc/>
  public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
  {
    if (limit <= 0)
    {
      yield break;
    }

    IAsyncEnumerable<(AstraDBMemoryEntry, double)> results = this._astraDbClient.GetNearestMatchesAsync(
        collectionName,
        embedding,
        limit,
        minRelevanceScore,
        withEmbeddings,
        cancellationToken);

    await foreach ((AstraDBMemoryEntry entry, double cosineSimilarity) in results.ConfigureAwait(false))
    {
      if (cosineSimilarity >= minRelevanceScore)
      {
        yield return (entry.ToMemoryRecord(), cosineSimilarity);
      }
    }
  }

  /// <inheritdoc/>
  public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
    string collectionName,
    ReadOnlyMemory<float> embedding,
    double minRelevanceScore = 0,
    bool withEmbedding = false,
    CancellationToken cancellationToken = default)
  {
    return await this.GetNearestMatchesAsync(
        collectionName: collectionName,
        embedding: embedding,
        limit: 1,
        minRelevanceScore: minRelevanceScore,
        withEmbeddings: withEmbedding,
        cancellationToken: cancellationToken).FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
  }

  #region private ================================================================================

  private readonly IAstraDBClient _astraDbClient;
  #endregion
}