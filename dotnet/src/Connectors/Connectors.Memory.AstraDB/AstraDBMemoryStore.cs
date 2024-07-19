using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;


namespace Microsoft.SemanticKernel.Connectors.AstraDB;

public class AstraDBMemoryStore
{
  /// <summary>
  /// Initializes a new instance of the <see cref="AstraDBMemoryStore"/> class.
  /// </summary>
  /// <param name="apiEndpoint">Astra DB API endpoint.</param>
  /// <param name="appToken">Application token for Astra DB.</param>
  /// <param name="keySpace">Name of the keyspace to work with.</param>
  /// <param name="vectorSize">Embedding vector size.</param>
  public AstraDBMemoryStore(string apiEndpoint, string appToken, string keySpace, int vectorSize)
  {
    this._astraDbClient = new AstraDBClient(apiEndpoint, appToken, keySpace, vectorSize);
  }

  public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
  {
    await this._astraDbClient.CreateCollectionAsync(collectionName).ConfigureAwait(false);
  }

  // / <summary>
  // / Gets all collection names in the data store.
  // / </summary>
  // / <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // / <returns>A group of collection names.</returns>
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


  /// <summary>
  /// Deletes a collection from the data store.
  /// </summary>
  /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param> b 
  public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default) =>
    await this._astraDbClient.DeleteCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);

  public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
  {
    // Verify.NotNullOrWhiteSpace(collectionName);
    record.Key = record.Metadata.Id;
    float[]? embeddingArray = record.Embedding.ToArray();

    await this._astraDbClient.UpsertAsync(
      collectionName,
      key: record.Key,
      metadata: record.GetSerializedMetadata(),
      embedding: embeddingArray,
      cancellationToken: cancellationToken).ConfigureAwait(false);

    return record.Key;

    // return await this._astraDbClient.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
  }

  public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
  {
    // Verify.NotNullOrWhiteSpace(collectionName);

    foreach (MemoryRecord record in records)
    {
      // Upsert each record asynchronously and yield return the key
      yield return await this.UpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
    }
  }

  public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
  {
    if (await DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
    {
      return await this._astraDbClient.FindOneAsync(collectionName, key, withEmbedding = false, cancellationToken).ConfigureAwait(false);
    }

    return null;
  }


  // /// <summary>
  // /// Upserts a memory record into the data store. Does not guarantee that the collection exists.
  // ///     If the record already exists, it will be updated.
  // ///     If the record does not exist, it will be created.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  // /// <param name="record">The memory record to upsert.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // /// <returns>The unique identifier for the memory record.</returns>
  // Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Upserts a group of memory records into the data store. Does not guarantee that the collection exists.
  // ///     If the record already exists, it will be updated.
  // ///     If the record does not exist, it will be created.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of vectors.</param>
  // /// <param name="records">The memory records to upsert.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // /// <returns>The unique identifiers for the memory records.</returns>
  // IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Gets a memory record from the data store. Does not guarantee that the collection exists.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  // /// <param name="key">The unique id associated with the memory record to get.</param>
  // /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // /// <returns>The memory record if found, otherwise null.</returns>
  // Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Gets a batch of memory records from the data store. Does not guarantee that the collection exists.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embedding.</param>
  // /// <param name="keys">The unique ids associated with the memory record to get.</param>
  // /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // /// <returns>The memory records associated with the unique keys provided.</returns>
  // IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Removes a memory record from the data store. Does not guarantee that the collection exists.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  // /// <param name="key">The unique id associated with the memory record to remove.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Removes a batch of memory records from the data store. Does not guarantee that the collection exists.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  // /// <param name="keys">The unique ids associated with the memory record to remove.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Gets the nearest matches to an embedding of type <see cref="float"/>. Does not guarantee that the collection exists.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  // /// <param name="embedding">The embedding to compare the collection's embeddings with.</param>
  // /// <param name="limit">The maximum number of similarity results to return.</param>
  // /// <param name="minRelevanceScore">The minimum cosine similarity threshold for returned results.</param>
  // /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
  // IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
  //     string collectionName,
  //     ReadOnlyMemory<float> embedding,
  //     int limit,
  //     double minRelevanceScore = 0.0,
  //     bool withEmbeddings = false,
  //     CancellationToken cancellationToken = default);

  // /// <summary>
  // /// Gets the nearest match to an embedding of type <see cref="float"/>. Does not guarantee that the collection exists.
  // /// </summary>
  // /// <param name="collectionName">The name associated with a collection of embeddings.</param>
  // /// <param name="embedding">The embedding to compare the collection's embeddings with.</param>
  // /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
  // /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
  // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
  // /// <returns>A tuple consisting of the <see cref="MemoryRecord"/> and the similarity score as a <see cref="double"/>. Null if no nearest match found.</returns>
  // Task<(MemoryRecord, double)?> GetNearestMatchAsync(
  //     string collectionName,
  //     ReadOnlyMemory<float> embedding,
  //     double minRelevanceScore = 0.0,
  //     bool withEmbedding = false,
  //     CancellationToken cancellationToken = default);
  #region private ================================================================================

  private readonly IAstraDBClient _astraDbClient;
  #endregion
}