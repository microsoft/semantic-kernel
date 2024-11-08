// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.Embeddings;
using OllamaSharp;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a embedding generation service using Ollama Original API.
/// </summary>
[Obsolete("Dedicated OllamaTextEmbeddingGenerationService is deprecated. Use OllamaApiClient.AsEmbeddingGenerationService() instead.")]
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
        this._textEmbeddingService = (ITextEmbeddingGenerationService)this._client.AsEmbeddingGenerationService();
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

        this._textEmbeddingService = (ITextEmbeddingGenerationService)this._client.AsEmbeddingGenerationService();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextEmbeddingGenerationService(
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(ollamaClient.SelectedModel, ollamaClient, loggerFactory)
    {
        this._textEmbeddingService = (ITextEmbeddingGenerationService)this._client.AsEmbeddingGenerationService();
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._textEmbeddingService.Attributes;

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => await this._textEmbeddingService.GenerateEmbeddingsAsync(data, kernel, cancellationToken).ConfigureAwait(false);

    #region Private

    private readonly ITextEmbeddingGenerationService _textEmbeddingService;

    #endregion
}
