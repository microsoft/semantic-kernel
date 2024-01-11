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
/// Represents a service for generating text using the Vertex AI Gemini API.
/// </summary>
public sealed class VertexAIGeminiTextGenerationService : GeminiTextGenerationServiceBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAIGeminiTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The model identifier.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public VertexAIGeminiTextGenerationService(
        string model,
        string apiKey,
        string location,
        string projectId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        var geminiConfiguration = new GeminiConfiguration(apiKey) { ModelId = model };
        this.TextGenerationClient = new VertexAIGeminiTextGenerationClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            configuration: geminiConfiguration,
            httpRequestFactory: new VertexAIGeminiHttpRequestFactory(apiKey),
            endpointProvider: new VertexAIGeminiEndpointProvider(new VertexAIConfiguration(location, projectId)),
            logger: loggerFactory?.CreateLogger(typeof(VertexAIGeminiTextGenerationService)));
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    internal VertexAIGeminiTextGenerationService(IGeminiTextGenerationClient client, string modelId)
    {
        this.TextGenerationClient = client;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
}
