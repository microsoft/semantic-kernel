// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// Interface for client managing postgres database operations.
/// </summary>
public interface IPostgresDbClient
{
    /// <summary>
    /// Check if a collection exists.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task<bool> DoesCollectionExistsAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all collections.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert entry into a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to upsert.</param>
    /// <param name="metadata">The metadata of the entry.</param>
    /// <param name="embedding">The embedding of the entry.</param>
    /// <param name="timestamp">The timestamp of the entry</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task UpsertAsync(string collectionName, string key, string? metadata, Vector? embedding, long? timestamp, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Vector"/>.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="embeddingFilter">The <see cref="Vector"/> to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    IAsyncEnumerable<(PostgresMemoryEntry, double)> GetNearestMatchesAsync(string collectionName, Vector embeddingFilter, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Read a entry by its key.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task<PostgresMemoryEntry?> ReadAsync(string collectionName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a entry by its key.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteAsync(string collectionName, string key, CancellationToken cancellationToken = default);
}
