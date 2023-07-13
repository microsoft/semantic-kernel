// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// Represents a generator of embeddings.
/// </summary>
/// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
/// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
public interface IEmbeddingGeneration<TValue, TEmbedding> : IAIService
    where TEmbedding : unmanaged
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    Task<IList<Embedding<TEmbedding>>> GenerateEmbeddingsAsync(IList<TValue> data, CancellationToken cancellationToken = default);
}
