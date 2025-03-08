// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Represents a client for interacting with the embeddings models by Google AI.
/// </summary>
internal sealed class GoogleAIEmbeddingClient : ClientBase
{
    private readonly string _embeddingModelId;
    private readonly Uri _embeddingEndpoint;
    private readonly int? _dimensions;

    /// <summary>
    /// Represents a client for interacting with the embeddings models by Google AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Embeddings generation model id</param>
    /// <param name="apiKey">Api key for GoogleAI endpoint</param>
    /// <param name="apiVersion">Version of the Google API</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    public GoogleAIEmbeddingClient(
        HttpClient httpClient,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion,
        ILogger? logger = null,
        int? dimensions = null)
        : base(
            httpClient: httpClient,
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._embeddingModelId = modelId;
        this._embeddingEndpoint = new Uri($"https://generativelanguage.googleapis.com/{versionSubLink}/models/{this._embeddingModelId}:batchEmbedContents?key={apiKey}");
        this._dimensions = dimensions;
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

        var geminiRequest = this.GetEmbeddingRequest(data);
        using var httpRequestMessage = await this.CreateHttpRequestAsync(geminiRequest, this._embeddingEndpoint).ConfigureAwait(false);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    private GoogleAIEmbeddingRequest GetEmbeddingRequest(IEnumerable<string> data)
        => GoogleAIEmbeddingRequest.FromData(data, this._embeddingModelId, this._dimensions);

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
        => ProcessEmbeddingsResponse(DeserializeResponse<GoogleAIEmbeddingResponse>(body));

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(GoogleAIEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Embeddings.Select(embedding => embedding.Values).ToList();
}
