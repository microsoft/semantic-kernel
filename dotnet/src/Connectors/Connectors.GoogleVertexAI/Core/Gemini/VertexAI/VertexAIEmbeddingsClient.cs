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
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.VertexAI;

/// <summary>
/// Represents a client for interacting with the embeddings models by Vertex AI.
/// </summary>
internal sealed class VertexAIEmbeddingsClient : ClientBase, IEmbeddingsClient
{
    private readonly string _embeddingModelId;

    /// <summary>
    /// Represents a client for interacting with the embeddings models by Vertex AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="configuration">Gemini configuration instance containing API key and other configuration options</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public VertexAIEmbeddingsClient(
        HttpClient httpClient,
        GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory:
            httpRequestFactory,
            endpointProvider: endpointProvider,
            logger: logger)
    {
        VerifyModelId(configuration);

        this._embeddingModelId = configuration.EmbeddingModelId!;
    }

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrEmpty(data);

        var endpoint = this.EndpointProvider.GetEmbeddingsEndpoint(this._embeddingModelId);
        var geminiRequest = this.GetEmbeddingRequest(data);
        using var httpRequestMessage = this.HTTPRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    #region PRIVATE METHODS

    private static void VerifyModelId(GeminiConfiguration configuration)
    {
        Verify.NotNullOrWhiteSpace(configuration?.EmbeddingModelId,
            $"{nameof(configuration)}.{nameof(configuration.EmbeddingModelId)}");
    }

    private VertexAIEmbeddingRequest GetEmbeddingRequest(IEnumerable<string> data)
        => VertexAIEmbeddingRequest.FromData(data, this._embeddingModelId);

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
        => ProcessEmbeddingsResponse(DeserializeResponse<VertexAIEmbeddingResponse>(body));

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(VertexAIEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Predictions.Select(prediction => prediction.Embeddings.Values).ToList();

    #endregion
}
