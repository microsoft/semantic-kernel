// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents a service for generating text embeddings using the Vertex AI Gemini API.
/// </summary>
public sealed class VertexAIEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly IEmbeddingGenerator<string, Embedding<float>> _generator;

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
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    public VertexAIEmbeddingGenerator(
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
        : this(modelId, () => new ValueTask<string>(bearerKey), location, projectId, apiVersion, httpClient, loggerFactory, dimensions)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        this._generator = new VertexAITextEmbeddingGenerationService(
            modelId: modelId,
            bearerKey: bearerKey,
            location: location,
            projectId: projectId,
            apiVersion: apiVersion,
            httpClient: httpClient,
            loggerFactory: loggerFactory,
            dimensions: dimensions)
            .AsEmbeddingGenerator();
#pragma warning restore CS0618 // Type or member is obsolete
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
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <remarks>
    /// This <paramref name="bearerTokenProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public VertexAIEmbeddingGenerator(
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        this._generator = new VertexAITextEmbeddingGenerationService(
            modelId: modelId,
            bearerTokenProvider: bearerTokenProvider,
            location: location,
            projectId: projectId,
            apiVersion: apiVersion,
            httpClient: httpClient,
            loggerFactory: loggerFactory,
            dimensions: dimensions)
            .AsEmbeddingGenerator();
#pragma warning restore CS0618 // Type or member is obsolete
    }

    /// <inheritdoc />
    public void Dispose()
        => this._generator.Dispose();

    /// <inheritdoc />
    public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
        => this._generator.GenerateAsync(values, options, cancellationToken);

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
        => this._generator.GetService(serviceType, serviceKey);
}
