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
/// Represents a service for generating text embeddings using the Google AI Gemini API.
/// </summary>
public sealed class GoogleAIEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly IEmbeddingGenerator<string, Embedding<float>> _generator;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAIEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="apiVersion">Version of the Google API</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    public GoogleAIEmbeddingGenerator(
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta, // todo: change beta to stable when stable version will be available
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        var generator = new GoogleAITextEmbeddingGenerationService(
            modelId: modelId,
            apiKey: apiKey,
            apiVersion: apiVersion,
            httpClient: httpClient,
            loggerFactory: loggerFactory,
            dimensions: dimensions);
#pragma warning restore CS0618 // Type or member is obsolete

        this._generator = generator.AsEmbeddingGenerator();
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
