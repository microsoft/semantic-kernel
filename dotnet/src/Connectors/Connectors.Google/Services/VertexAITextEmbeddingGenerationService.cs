// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents a service for generating text embeddings using the Vertex AI Gemini API.
/// </summary>
[Obsolete("Use VertexAIEmbeddingGenerator instead.")]
public sealed class VertexAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly VertexAIEmbeddingClient _embeddingClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="VertexAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request.</param>
    /// <param name="projectId">Your Project Id.</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public VertexAITextEmbeddingGenerationService(
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
        : this(modelId, () => new ValueTask<string>(bearerKey), location, projectId, apiVersion, httpClient, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(bearerKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VertexAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="bearerTokenProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request.</param>
    /// <param name="projectId">Your Project Id.</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    /// <remarks>
    /// This <paramref name="bearerTokenProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public VertexAITextEmbeddingGenerationService(
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(bearerTokenProvider);
        Verify.NotNullOrWhiteSpace(location);
        Verify.NotNullOrWhiteSpace(projectId);

        this._embeddingClient = new VertexAIEmbeddingClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: modelId,
            bearerTokenProvider: bearerTokenProvider,
            location: location,
            projectId: projectId,
            apiVersion: apiVersion,
            logger: loggerFactory?.CreateLogger(typeof(VertexAITextEmbeddingGenerationService)));
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._embeddingClient.GenerateEmbeddingsAsync(data, cancellationToken);
    }
}
