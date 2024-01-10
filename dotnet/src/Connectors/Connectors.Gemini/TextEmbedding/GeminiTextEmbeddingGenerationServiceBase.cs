#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

public class GeminiTextEmbeddingGenerationServiceBase : ITextEmbeddingGenerationService
{
    private protected Dictionary<string, object?> AttributesInternal { get; } = new();
    private protected IGeminiClient Client { get; init; }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.Client.GenerateEmbeddingsAsync(data, cancellationToken);
    }
}
