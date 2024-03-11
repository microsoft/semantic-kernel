// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;

/// <summary>
/// Represents a client for interacting with the embeddings models by Vertex AI.
/// </summary>
internal sealed class VertexAIEmbeddingClient : ClientBase
{
    private readonly string _embeddingModelId;
    private readonly Uri _embeddingEndpoint;

    /// <summary>
    /// Represents a client for interacting with the embeddings models by Vertex AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Embeddings generation model id</param>
    /// <param name="bearerKey">Bearer key used for authentication</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Project ID from google cloud</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public VertexAIEmbeddingClient(
        HttpClient httpClient,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            logger: logger,
            bearerKey: bearerKey)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(location);
        Verify.NotNullOrWhiteSpace(projectId);

        this._embeddingModelId = modelId;
        this._embeddingEndpoint = new Uri($"https://{location}-aiplatform.googleapis.com/v1/projects/{projectId}/locations/{location}/publishers/google/models/{this._embeddingModelId}:predict");
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

        var geminiRequest = GetEmbeddingRequest(data);
        using var httpRequestMessage = this.CreateHttpRequest(geminiRequest, this._embeddingEndpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    private static VertexAIEmbeddingRequest GetEmbeddingRequest(IEnumerable<string> data)
        => VertexAIEmbeddingRequest.FromData(data);

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
        => ProcessEmbeddingsResponse(DeserializeResponse<VertexAIEmbeddingResponse>(body));

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(VertexAIEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Predictions.Select(prediction => prediction.Embeddings.Values).ToList();
}
