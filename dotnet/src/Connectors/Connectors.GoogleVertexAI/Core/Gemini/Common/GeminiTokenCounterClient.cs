// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.Common;

/// <summary>
/// Represents a client for token counting gemini model.
/// </summary>
internal class GeminiTokenCounterClient : GeminiClient, IGeminiTokenCounterClient
{
    private readonly string _modelId;

    /// <summary>
    /// Represents a client for token counting gemini model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="configuration">Gemini configuration instance containing API key and other configuration options</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiTokenCounterClient(
        HttpClient httpClient,
        GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            logger: logger)
    {
        VerifyModelId(configuration);

        this._modelId = configuration.ModelId!;
    }

    /// <inheritdoc/>
    public virtual async Task<int> CountTokensAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = this.EndpointProvider.GetCountTokensEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HTTPRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessCountTokensResponse(body);
    }

    private static int DeserializeAndProcessCountTokensResponse(string body)
    {
        var node = DeserializeResponse<JsonNode>(body);
        return node["totalTokens"]?.GetValue<int>() ?? throw new KernelException("Invalid response from model");
    }

    private static void VerifyModelId(GeminiConfiguration configuration)
    {
        Verify.NotNullOrWhiteSpace(configuration.ModelId, $"{nameof(configuration)}.{nameof(configuration.ModelId)}");
    }
}
