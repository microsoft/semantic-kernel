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
    Task<string?> FindOneAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default);
  }
}
