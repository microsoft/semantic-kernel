// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Represents a client for interacting with the embeddings models by Vertex AI.
/// </summary>
internal sealed class VertexAIEmbeddingClient : ClientBase
{
    private readonly string _embeddingModelId;
    private readonly VertexAIVersion _apiVersion;
    private readonly string _location;
    private readonly string _projectId;
    private readonly Uri _embeddingEndpoint;
    private readonly int? _dimensions;

    /// <summary>
    /// Represents a client for interacting with the embeddings models by Vertex AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Embeddings generation model id</param>
    /// <param name="bearerTokenProvider">Bearer key provider used for authentication</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Project ID from google cloud</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    public VertexAIEmbeddingClient(
        HttpClient httpClient,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion,
        ILogger? logger = null,
        int? dimensions = null)
        : base(
            httpClient: httpClient,
            logger: logger,
            bearerTokenProvider: bearerTokenProvider)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(location);
        Verify.ValidHostnameSegment(location);
        Verify.NotNullOrWhiteSpace(projectId);

        string versionSubLink = GetApiVersionSubLink(apiVersion);
        string baseUri = GetVertexAIBaseUri(location);

        this._apiVersion = apiVersion;
        this._location = location;
        this._projectId = projectId;
        this._embeddingModelId = modelId;
        this._embeddingEndpoint = new Uri($"{baseUri}/{versionSubLink}/projects/{projectId}/locations/{location}/publishers/google/models/{this._embeddingModelId}:predict");
        this._dimensions = dimensions;
    }

    private Uri GetEmbeddingEndpoint(string modelId)
    {
        string versionSubLink = GetApiVersionSubLink(this._apiVersion);
        string baseUri = GetVertexAIBaseUri(this._location);
        return new Uri($"{baseUri}/{versionSubLink}/projects/{this._projectId}/locations/{this._location}/publishers/google/models/{modelId}:predict");
    }

    /// <summary>
    /// Generates embeddings for the given data asynchronously.
    /// </summary>
    /// <param name="data">The list of strings to generate embeddings for.</param>
    /// <param name="options">The embedding generation options.</param>
    /// <param name="cancellationToken">The cancellation token to cancel the operation.</param>
    /// <returns>Result contains a list of read-only memories of floats representing the generated embeddings.</returns>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        EmbeddingGenerationOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrEmpty(data);

        string modelId = !string.IsNullOrWhiteSpace(options?.ModelId) ? options.ModelId : this._embeddingModelId;
        var geminiRequest = this.GetEmbeddingRequest(data, options);
        var endpoint = modelId == this._embeddingModelId ? this._embeddingEndpoint : this.GetEmbeddingEndpoint(modelId);
        using var httpRequestMessage = await this.CreateHttpRequestAsync(geminiRequest, endpoint).ConfigureAwait(false);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    private VertexAIEmbeddingRequest GetEmbeddingRequest(IEnumerable<string> data, EmbeddingGenerationOptions? options = null)
        => VertexAIEmbeddingRequest.FromData(data, options?.Dimensions ?? this._dimensions);

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
        => ProcessEmbeddingsResponse(DeserializeResponse<VertexAIEmbeddingResponse>(body));

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(VertexAIEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Predictions.Select(prediction => prediction.Embeddings.Values).ToList();
}
