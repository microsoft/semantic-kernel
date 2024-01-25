// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a client for interacting with the text generation gemini models by Vertex AI.
/// </summary>
// todo: remove this class when gemini vertex ai (preview api) support non-streaming chat completion
internal sealed class VertexAIGeminiTextGenerationClient : GeminiTextGenerationClient, IGeminiTextGenerationClient
{
    /// <summary>
    /// Represents a client for interacting with the text generation gemini models by Vertex AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting text generation</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public VertexAIGeminiTextGenerationClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null) : base(
        chatCompletionClient: new VertexAIGeminiChatCompletionClient(
            httpClient: httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            streamJsonParser: streamJsonParser,
            logger: logger))
    { }
}
