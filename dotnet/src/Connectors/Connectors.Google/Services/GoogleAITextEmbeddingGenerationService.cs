// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents a service for generating text embeddings using the Google AI Gemini API.
/// </summary>
[Obsolete("Use GoogleAIEmbeddingGenerator instead.")]
public sealed class GoogleAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly GoogleAIEmbeddingClient _embeddingClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="apiVersion">Version of the Google API</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    public GoogleAITextEmbeddingGenerationService(
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta, // todo: change beta to stable when stable version will be available
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._embeddingClient = new GoogleAIEmbeddingClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: modelId,
            apiKey: apiKey,
            apiVersion: apiVersion,
            logger: loggerFactory?.CreateLogger(typeof(GoogleAITextEmbeddingGenerationService)),
            dimensions: dimensions);
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);

        if (dimensions.HasValue)
        {
            this._attributesInternal.Add(EmbeddingGenerationExtensions.DimensionsKey, dimensions);
        }
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._embeddingClient.GenerateEmbeddingsAsync(data, null, cancellationToken);
    }

    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="options">Additional options for embedding generation</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    /// <remarks>
    /// <para>
    /// The <paramref name="options"/> parameter can be used to override default settings such as <see cref="EmbeddingGenerationOptions.ModelId"/> and <see cref="EmbeddingGenerationOptions.Dimensions"/>
    /// </para>
    /// <para>
    /// Additionally a key/value of <c>"taskType"</c> can be provided in the <see cref="EmbeddingGenerationOptions.AdditionalProperties"/> for specific embedding tasks.
    /// </para>
    /// </remarks>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        EmbeddingGenerationOptions? options,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._embeddingClient.GenerateEmbeddingsAsync(data, options, cancellationToken);
    }
}
