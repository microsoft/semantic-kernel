// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Memory;

/// <summary>
/// An interface for semantic memory that creates and recalls memories associated with text.
/// </summary>
public interface ISemanticTextMemory
{
    /// <summary>
    /// Save some information into the semantic memory, keeping a copy of the source information.
    /// </summary>
    /// <param name="collection">Collection where to save the information.</param>
    /// <param name="text">Information to save.</param>
    /// <param name="id">Unique identifier.</param>
    /// <param name="description">Optional description.</param>
    /// <param name="additionalMetadata">Optional string for saving custom metadata.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Unique identifier of the saved memory record.</returns>
    public Task<string> SaveInformationAsync(
        string collection,
        string text,
        string id,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Save some information into the semantic memory, keeping only a reference to the source information.
    /// </summary>
    /// <param name="collection">Collection where to save the information.</param>
    /// <param name="text">Information to save.</param>
    /// <param name="externalId">Unique identifier, e.g. URL or GUID to the original source.</param>
    /// <param name="externalSourceName">Name of the external service, e.g. "MSTeams", "GitHub", "WebSite", "Outlook IMAP", etc.</param>
    /// <param name="description">Optional description.</param>
    /// <param name="additionalMetadata">Optional string for saving custom metadata.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Unique identifier of the saved memory record.</returns>
    public Task<string> SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Fetch a memory by key.
    /// For local memories the key is the "id" used when saving the record.
    /// For external reference, the key is the "URI" used when saving the record.
    /// </summary>
    /// <param name="collection">Collection to search.</param>
    /// <param name="key">Unique memory record identifier.</param>
    /// <param name="withEmbedding">Whether to return the embedding of the memory found.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Memory record, or null when nothing is found</returns>
    public Task<MemoryQueryResult?> GetAsync(string collection, string key, bool withEmbedding = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Remove a memory by key.
    /// For local memories the key is the "id" used when saving the record.
    /// For external reference, the key is the "URI" used when saving the record.
    /// </summary>
    /// <param name="collection">Collection to search.</param>
    /// <param name="key">Unique memory record identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task RemoveAsync(string collection, string key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Find some information in memory
    /// </summary>
    /// <param name="collection">Collection to search</param>
    /// <param name="query">What to search for</param>
    /// <param name="limit">How many results to return</param>
    /// <param name="minRelevanceScore">Minimum relevance score, from 0 to 1, where 1 means exact match.</param>
    /// <param name="withEmbeddings">Whether to return the embeddings of the memories found.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Memories found</returns>
    public IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.7,
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a group of all available collection names.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A group of collection names.</returns>
    public Task<IList<string>> GetCollectionsAsync(CancellationToken cancellationToken = default);
}
