// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace;

/// <summary>
/// HuggingFace embedding generation service.
/// </summary>
public sealed class HuggingFaceEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly bool _isExternalHttpClient;
    private readonly HttpClient _httpClient;
    private readonly EmbeddingGeneratorMetadata _metadata;
    private HuggingFaceClient Client { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="modelId">The HuggingFace model for the text generation service.</param>
    /// <param name="endpoint">The endpoint uri including the port where HuggingFace server is hosted</param>
    /// <param name="apiKey">Optional API key for accessing the HuggingFace service.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the HuggingFace API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public HuggingFaceEmbeddingGenerator(
        string modelId,
        Uri? endpoint = null,
        string? apiKey = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._isExternalHttpClient = httpClient is not null;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);

        this.Client = new HuggingFaceClient(
        modelId: modelId,
            endpoint: endpoint ?? this._httpClient.BaseAddress,
            apiKey: apiKey,
            httpClient: this._httpClient,
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this._metadata = new EmbeddingGeneratorMetadata(providerUri: endpoint, defaultModelId: modelId);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="endpoint">The endpoint uri including the port where HuggingFace server is hosted</param>
    /// <param name="apiKey">Optional API key for accessing the HuggingFace service.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the HuggingFace API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public HuggingFaceEmbeddingGenerator(
        Uri endpoint,
        string? apiKey = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(endpoint);

        this._isExternalHttpClient = httpClient is not null;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);

        this.Client = new HuggingFaceClient(
            modelId: null,
            endpoint: endpoint ?? this._httpClient.BaseAddress,
            apiKey: apiKey,
            httpClient: this._httpClient,
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this._metadata = new EmbeddingGeneratorMetadata(providerUri: endpoint);
    }

    /// <inheritdoc/>
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
    {
        var data = values.ToList();
        var result = await this.Client.GenerateEmbeddingsAsync(data, null, cancellationToken).ConfigureAwait(false);
        return new GeneratedEmbeddings<Embedding<float>>(result.Select(e => new Embedding<float>(e)));
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        // Dispose the HttpClient only if it was created internally
        if (!this._isExternalHttpClient)
        {
            this._httpClient.Dispose();
        }
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            serviceType == typeof(EmbeddingGeneratorMetadata) ? this._metadata :
            null;
    }
}
