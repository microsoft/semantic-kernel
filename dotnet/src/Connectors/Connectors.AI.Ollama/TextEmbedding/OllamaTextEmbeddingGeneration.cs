// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextEmbedding;

/// <summary>
/// Ollama embedding generation service.
/// </summary>
public sealed class OllamaTextEmbeddingGeneration : ITextEmbeddingGeneration
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGeneration"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public OllamaTextEmbeddingGeneration(Uri endpoint, string model)
    {
    }

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException("Embeddings capability is not supported");
    }

    #region private ================================================================================
    #endregion
}
