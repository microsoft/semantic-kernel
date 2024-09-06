// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using OllamaSharp;
using OllamaSharp.Models;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a embedding generation service using Ollama Original API.
/// </summary>
public sealed class OllamaTextEmbeddingGenerationService : ServiceBase, ITextEmbeddingGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextEmbeddingGenerationService(
        string modelId,
        Uri endpoint,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, endpoint, null, loggerFactory)
    {
        Verify.NotNull(endpoint);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="httpClient">HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextEmbeddingGenerationService(
        string modelId,
        HttpClient httpClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, null, httpClient, loggerFactory)
    {
        Verify.NotNull(httpClient);
        Verify.NotNull(httpClient.BaseAddress);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextEmbeddingGenerationService(
        string modelId,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, ollamaClient, loggerFactory)
    {
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var request = new EmbedRequest
        {
            Model = this.GetModelId()!,
            Input = data.ToList(),
        };

        var response = await this._client.Embed(request, cancellationToken: cancellationToken).ConfigureAwait(false);

        List<ReadOnlyMemory<float>> embeddings = [];
        foreach (var embedding in response.Embeddings)
        {
            embeddings.Add(embedding.Select(@decimal => (float)@decimal).ToArray());
        }

        return embeddings;
    }
}
