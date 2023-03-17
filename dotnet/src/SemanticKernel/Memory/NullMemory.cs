// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Implementation of <see cref="ISemanticTextMemory"/> that stores nothing.
/// </summary>
public sealed class NullMemory : ISemanticTextMemory
{
    /// <summary>
    /// Singleton instance
    /// </summary>
    public static NullMemory Instance { get; } = new();

    /// <inheritdoc/>
    public Task SaveInformationAsync(
        string collection,
        string text,
        string id,
        string? description = null,
        CancellationToken cancel = default)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        CancellationToken cancel = default)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task<MemoryQueryResult?> GetAsync(
        string collection,
        string key,
        CancellationToken cancel = default)
    {
        return Task.FromResult(null as MemoryQueryResult);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.7,
        CancellationToken cancel = default)
    {
        return AsyncEnumerable.Empty<MemoryQueryResult>();
    }

    /// <inheritdoc/>
    public Task<IList<string>> GetCollectionsAsync(
        CancellationToken cancel = default)
    {
        return Task.FromResult(new List<string>() as IList<string>);
    }

    private NullMemory()
    {
    }
}
