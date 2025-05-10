// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral text embedding service.
/// </summary>
[Obsolete("Use MistralAIEmbeddingGenerator instead.")]
public sealed class MistralAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MistralAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The Mistral modelId for the text generation service.</param>
    /// <param name="apiKey">API key for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional  uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the MistralAI API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public MistralAITextEmbeddingGenerationService(string modelId, string apiKey, Uri? endpoint = null, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null)
    {
        this.Client = new MistralClient(
            modelId: modelId,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GenerateEmbeddingsAsync(data, cancellationToken, executionSettings: null, kernel);

    #region private
    private Dictionary<string, object?> AttributesInternal { get; } = [];
    private MistralClient Client { get; }
    #endregion
}
