#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using Microsoft.SemanticKernel.Connectors.Gemini.Core.GoogleAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

/// <summary>
/// Represents a service for generating text using the Google AI Gemini API.
/// </summary>
public sealed class GoogleAIGeminiTextGenerationService : GeminiTextGenerationServiceBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAIGeminiTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The model identifier.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public GoogleAIGeminiTextGenerationService(
        string model,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        var geminiConfiguration = new GeminiConfiguration(apiKey) { ModelId = model };
        this.Client = new GoogleAIGeminiClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            configuration: geminiConfiguration,
            httpRequestFactory: new GoogleAIGeminiHttpRequestFactory(),
            endpointProvider: new GoogleAIGeminiEndpointProvider(apiKey),
            logger: loggerFactory?.CreateLogger(typeof(GoogleAIGeminiTextGenerationService)));
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    internal GoogleAIGeminiTextGenerationService(IGeminiClient client)
    {
        this.Client = client;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, client.ModelId);
    }
}
