#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.VertexAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a service for generating text embeddings using the Vertex AI Gemini API.
/// </summary>
public sealed class VertexAIGeminiTextEmbeddingGenerationService : GeminiTextEmbeddingGenerationServiceBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAIGeminiTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="model">The model identifier.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public VertexAIGeminiTextEmbeddingGenerationService(
        string model,
        string apiKey,
        string location,
        string projectId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        var geminiConfiguration = new GeminiConfiguration(apiKey) { EmbeddingModelId = model };
        this.EmbeddingsClient = new VertexAIEmbeddingsClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            configuration: geminiConfiguration,
            httpRequestFactory: new VertexAIGeminiHttpRequestFactory(apiKey),
            endpointProvider: new VertexAIGeminiEndpointProvider(new VertexAIConfiguration(location, projectId)),
            logger: loggerFactory?.CreateLogger(typeof(VertexAIGeminiTextEmbeddingGenerationService)));
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    internal VertexAIGeminiTextEmbeddingGenerationService(IEmbeddingsClient client, string embeddingModelId)
    {
        this.EmbeddingsClient = client;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, embeddingModelId);
    }
}
