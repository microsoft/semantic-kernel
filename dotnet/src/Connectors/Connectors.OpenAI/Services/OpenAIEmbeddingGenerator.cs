// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;
using OpenAI;

#pragma warning disable CS0618 // Type or member is obsolete

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI implementation of <see cref="ITextEmbeddingGenerationService"/>
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAIEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly ClientCore _client;
    private readonly EmbeddingGeneratorMetadata _metadata;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIEmbeddingGenerator(
        string modelId,
        string apiKey,
        string? organization = null,
        int? dimensions = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        this._client = new(
            modelId: modelId,
            apiKey: apiKey,
            endpoint: null,
            organizationId: organization,
            httpClient: httpClient,
            logger: loggerFactory?.CreateLogger(typeof(OpenAIEmbeddingGenerator)));

        this._metadata = new EmbeddingGeneratorMetadata(
            defaultModelId: modelId,
            providerName: organization,
            defaultModelDimensions: dimensions);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIEmbeddingGenerator(
        string modelId,
        OpenAIClient openAIClient,
        int? dimensions = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        this._client = new(modelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAIEmbeddingGenerator)));

        this._metadata = new EmbeddingGeneratorMetadata(
            defaultModelId: modelId,
            defaultModelDimensions: dimensions);
    }

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._client.LogActionDetails();
        return this._client.GetEmbeddingsAsync(this._client.ModelId, data, kernel, this._metadata.DefaultModelDimensions, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
    {
        var result = await this._client.GetEmbeddingsAsync(this._client.ModelId, values.ToList(), kernel: null, options?.Dimensions ?? this._metadata.DefaultModelDimensions, cancellationToken).ConfigureAwait(false);
        return new(result.Select(e => new Embedding<float>(e)));
    }

    /// <inheritdoc />
    public void Dispose()
    {
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            serviceType == typeof(EmbeddingGeneratorMetadata) ? this._metadata :
            null;
    }
}
