#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.GoogleAI;

/// <summary>
/// Represents a client for interacting with the Gemini API by Google AI.
/// </summary>
internal sealed class GoogleAIGeminiClient : GeminiClient
{
    /// <summary>
    /// Represents a client for interacting with the Gemini API by Google AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="configuration">Gemini configuration instance containing API key and other configuration options</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Stream Json Parser instance used for parsing JSON responses stream (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GoogleAIGeminiClient(
        HttpClient httpClient, GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(httpClient, configuration, httpRequestFactory, endpointProvider, streamJsonParser, logger) { }

    /// <inheritdoc/>
    public override async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        CancellationToken cancellationToken = default)
    {
        this.VerifyEmbeddingModelId();
        Verify.NotNullOrEmpty(data);

        var endpoint = this.EndpointProvider.GetEmbeddingsEndpoint(this.EmbeddingModelId);
        var geminiRequest = this.GetGeminiEmbeddingRequest(data);
        using var httpRequestMessage = this.HTTPRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    private GoogleAIEmbeddingRequest GetGeminiEmbeddingRequest(IEnumerable<string> data)
    {
        this.VerifyEmbeddingModelId();
        return GoogleAIEmbeddingRequest.FromData(data, this.EmbeddingModelId);
    }

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
    {
        var embeddingsResponse = DeserializeResponse<GoogleAIEmbeddingResponse>(body);
        return ProcessEmbeddingsResponse(embeddingsResponse);
    }

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(GoogleAIEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Embeddings.Select(embedding => embedding.Values).ToList();
}
