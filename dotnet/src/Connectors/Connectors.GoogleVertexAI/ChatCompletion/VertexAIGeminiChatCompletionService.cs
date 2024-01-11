#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.VertexAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a chat completion service using Vertex AI Gemini API.
/// </summary>
public sealed class VertexAIGeminiChatCompletionService : GeminiChatCompletionServiceBase
{
    /// <summary>
    /// Initializes a new instance of the GeminiChatCompletionService class.
    /// </summary>
    /// <param name="model">The Gemini model for the chat completion service.</param>
    /// <param name="apiKey">The API key for authentication with the Gemini client.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Gemini API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    [SuppressMessage(
        "Reliability",
        "CA2000:Dispose objects before losing scope",
        Justification = "HttpClient is disposed by the HttpClientProvider")]
    public VertexAIGeminiChatCompletionService(
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
        this.ChatCompletionClient = new VertexAIGeminiChatCompletionClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            configuration: geminiConfiguration,
            httpRequestFactory: new VertexAIGeminiHttpRequestFactory(apiKey),
            endpointProvider: new VertexAIGeminiEndpointProvider(new VertexAIConfiguration(location, projectId)),
            logger: loggerFactory?.CreateLogger(typeof(GoogleAIGeminiChatCompletionService)));
        this.TextGenerationClient = new VertexAIGeminiTextGenerationClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            configuration: geminiConfiguration,
            httpRequestFactory: new VertexAIGeminiHttpRequestFactory(apiKey),
            endpointProvider: new VertexAIGeminiEndpointProvider(new VertexAIConfiguration(location, projectId)),
            logger: loggerFactory?.CreateLogger(typeof(GoogleAIGeminiTextGenerationService)));
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    internal VertexAIGeminiChatCompletionService(
        IGeminiChatCompletionClient chatCompletionClient,
        IGeminiTextGenerationClient textGenerationClient,
        string modelId)
    {
        this.ChatCompletionClient = chatCompletionClient;
        this.TextGenerationClient = textGenerationClient;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
}
