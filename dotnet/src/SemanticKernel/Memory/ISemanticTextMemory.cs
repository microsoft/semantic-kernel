// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An interface for semantic memory that creates and recalls memories associated with text.
/// </summary>
public interface ISemanticTextMemory
{
    /// <summary>
    /// Save some information into the semantic memory, keeping a copy of the source information.
    /// </summary>
    /// <param name="collection">Collection where to save the information</param>
    /// <param name="id">Unique identifier</param>
    /// <param name="text">Information to save</param>
    /// <param name="description">Optional description</param>
    /// <param name="cancel">Cancellation token</param>
    public Task SaveInformationAsync(
        string collection,
        string text,
        string id,
        string? description = null,
        CancellationToken cancel = default);

    /// <summary>
    /// Save some information into the semantic memory, keeping only a reference to the source information.
    /// </summary>
    /// <param name="collection">Collection where to save the information</param>
    /// <param name="text">Information to save</param>
    /// <param name="externalId">Unique identifier, e.g. URL or GUID to the original source</param>
    /// <param name="externalSourceName">Name of the external service, e.g. "MSTeams", "GitHub", "WebSite", "Outlook IMAP", etc.</param>
    /// <param name="description">Optional description</param>
    /// <param name="cancel">Cancellation token</param>
    public Task SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        CancellationToken cancel = default);

    /// <summary>
    /// Fetch a memory by key.
    /// For local memories the key is the "id" used when saving the record.
    /// For external reference, the key is the "URI" used when saving the record.
    /// </summary>
    /// <param name="collection">Collection to search</param>
    /// <param name="key">Unique memory record identifier</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>Memory record, or null when nothing is found</returns>
    public Task<MemoryQueryResult?> GetAsync(string collection, string key, CancellationToken cancel = default);

    /// <summary>
    /// Find some information in memory
    /// </summary>
    /// <param name="collection">Collection to search</param>
    /// <param name="query">What to search for</param>
    /// <param name="limit">How many results to return</param>
    /// <param name="minRelevanceScore">Minimum relevance score, from 0 to 1, where 1 means exact match.</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>Memories found</returns>
    public IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.7,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets a group of all available collection names.
    /// </summary>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A group of collection names.</returns>
    public Task<IList<string>> GetCollectionsAsync(CancellationToken cancel = default);
}
