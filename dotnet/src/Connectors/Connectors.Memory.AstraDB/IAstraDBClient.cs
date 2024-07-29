using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;


namespace Microsoft.SemanticKernel.Connectors.AstraDB
{
  /// <summary>
  /// Interface for client managing AstraDB database operations.
  /// </summary>
  public interface IAstraDBClient
  {
    /// <summary>
    /// Creates a collection in the AstraDB database.
    /// </summary>
    /// <param name="collectionName">The name assigned to the collection.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a collection of names from Astra DB.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous stream of collection names.</returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a Collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert entry into a Collection.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="key">The key of the entry to upsert.</param>
    /// <param name="metadata">The metadata of the entry.</param>
    /// <param name="embedding">The embedding of the entry.</param>
    /// <param name="timestamp">The timestamp of the entry. Its 'DateTimeKind' must be <see cref="DateTimeKind.Utc"/></param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task UpsertAsync(string collectionName, string key, string? metadata, float[]? embedding, CancellationToken cancellationToken = default);

    /// <summary>
    /// Finds a document in the collection by its key.
    /// </summary>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="key">The key of the document to find.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The found document as a JSON string, or null if not found.</returns>
    Task<MemoryRecord?> FindOneAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default);

    /// </summary>
    /// <param name="collectionName">The name of the collection from which the document will be deleted.</param>
    /// <param name="key">The key of the document to be deleted.</param>
    /// <param name="cancellationToken">A cancellation token that can be used by other objects or threads to receive notice of cancellation.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    Task DeleteOneAsync(string collectionName, string key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes multiple entries from a specified collection in the AstraDB.
    /// </summary>
    /// <param name="collectionName">The name of the collection from which entries are to be deleted.</param>
    /// <param name="keys">An enumerable list of keys identifying the entries to be deleted.</param>
    /// <param name="cancellationToken">An optional token to cancel the asynchronous operation.</param>
    /// <returns>A task that represents the asynchronous delete operation.</returns>
    Task DeleteManyAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieves the nearest matches to a given embedding from a specified collection in AstraDB.
    /// </summary>
    /// <param name="collectionName">The name of the collection to search for matches.</param>
    /// <param name="embedding">The embedding vector to compare against stored entries.</param>
    /// <param name="limit">The maximum number of matches to return.</param>
    /// <param name="minRelevanceScore">The minimum similarity score required for a match to be included in the results. Defaults to 0.</param>
    /// <param name="withEmbeddings">Indicates whether to include the embeddings in the results. Defaults to false.</param>
    /// <param name="cancellationToken">An optional token to cancel the asynchronous operation.</param>
    /// <returns>
    IAsyncEnumerable<(AstraDBMemoryEntry, double)> GetNearestMatchesAsync(
            string collectionName,
            ReadOnlyMemory<float> embedding,
            int limit,
            double minRelevanceScore = 0,
            bool withEmbeddings = false,
            CancellationToken cancellationToken = default);
  }
}
