// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Reranking;

/// <summary>
/// Interface for text reranking services that can reorder documents based on relevance to a query.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextRerankingService : IAIService
{
    /// <summary>
    /// Reranks a list of documents based on their relevance to a query.
    /// </summary>
    /// <param name="query">The query to rank documents against.</param>
    /// <param name="documents">The list of documents to rerank.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>A list of <see cref="RerankResult"/> sorted by relevance score in descending order.</returns>
    Task<IList<RerankResult>> RerankAsync(
        string query,
        IList<string> documents,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}
