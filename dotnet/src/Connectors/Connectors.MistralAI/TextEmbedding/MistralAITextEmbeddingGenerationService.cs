// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral text embedding service.
/// </summary>
public sealed class MistralAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MistralAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="model">The Mistral model for the text generation service.</param>
    /// <param name="endpoint">The uri endpoint including the port where HuggingFace server is hosted</param>
    /// <param name="apiKey">Optional API key for accessing the HuggingFace service.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the HuggingFace API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public MistralAITextEmbeddingGenerationService(string model, Uri? endpoint, string? apiKey, HttpClient httpClient, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this.Client = new MistralClient(
        modelId: model,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
#pragma warning disable CA2000 // Dispose objects before losing scope
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000 // Dispose objects before losing scope
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GenerateEmbeddingsAsync(data, kernel, cancellationToken);

    #region private
    private Dictionary<string, object?> AttributesInternal { get; } = new();
    private MistralClient Client { get; }
    #endregion
}
