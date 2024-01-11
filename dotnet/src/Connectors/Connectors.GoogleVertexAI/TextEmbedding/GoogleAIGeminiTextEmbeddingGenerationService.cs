#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.GoogleAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a service for generating text embeddings using the Google AI Gemini API.
/// </summary>
public sealed class GoogleAIGeminiTextEmbeddingGenerationService : GeminiTextEmbeddingGenerationServiceBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAIGeminiTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="model">The model identifier.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public GoogleAIGeminiTextEmbeddingGenerationService(
        string model,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        var geminiConfiguration = new GeminiConfiguration(apiKey) { EmbeddingModelId = model };
        this.EmbeddingsClient = new GoogleAIEmbeddingsClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            configuration: geminiConfiguration,
            httpRequestFactory: new GoogleAIGeminiHttpRequestFactory(),
            endpointProvider: new GoogleAIGeminiEndpointProvider(apiKey),
            logger: loggerFactory?.CreateLogger(typeof(GoogleAIGeminiTextEmbeddingGenerationService)));
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    internal GoogleAIGeminiTextEmbeddingGenerationService(IEmbeddingsClient client, string embeddingModelId)
    {
        this.EmbeddingsClient = client;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, embeddingModelId);
    }
}
