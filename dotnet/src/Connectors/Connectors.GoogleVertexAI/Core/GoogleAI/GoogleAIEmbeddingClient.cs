// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a client for interacting with the embeddings models by Google AI.
/// </summary>
internal sealed class GoogleAIEmbeddingClient : ClientBase
{
    private readonly string _embeddingModelId;

    /// <summary>
    /// Represents a client for interacting with the embeddings models by Google AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="embeddingModelId">Embeddings generation model id</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GoogleAIEmbeddingClient(
        HttpClient httpClient,
        string embeddingModelId,
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
        Verify.NotNullOrWhiteSpace(embeddingModelId);
        this._embeddingModelId = embeddingModelId;
    }

    /// <summary>
    /// Generates embeddings for the given data asynchronously.
    /// </summary>
    /// <param name="data">The list of strings to generate embeddings for.</param>
    /// <param name="cancellationToken">The cancellation token to cancel the operation.</param>
    /// <returns>Result contains a list of read-only memories of floats representing the generated embeddings.</returns>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrEmpty(data);

        var endpoint = this.EndpointProvider.GetEmbeddingsEndpoint(this._embeddingModelId);
        var geminiRequest = this.GetEmbeddingRequest(data);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    private GoogleAIEmbeddingRequest GetEmbeddingRequest(IEnumerable<string> data)
        => GoogleAIEmbeddingRequest.FromData(data, this._embeddingModelId);

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
        => ProcessEmbeddingsResponse(DeserializeResponse<GoogleAIEmbeddingResponse>(body));

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(GoogleAIEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Embeddings.Select(embedding => embedding.Values).ToList();
}
