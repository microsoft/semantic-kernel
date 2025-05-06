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
public sealed class OpenAITextEmbeddingGenerationService : ITextEmbeddingGenerationService, IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly ClientCore _client;
    private readonly int? _dimensions;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    public OpenAITextEmbeddingGenerationService(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        this._client = new(
            modelId: modelId,
            apiKey: apiKey,
            endpoint: null,
            organizationId: organization,
            httpClient: httpClient,
            logger: loggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGenerationService)));

        this._dimensions = dimensions;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    public OpenAITextEmbeddingGenerationService(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        this._client = new(modelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGenerationService)));
        this._dimensions = dimensions;
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._client.LogActionDetails();
        return this._client.GetEmbeddingsAsync(this._client.ModelId, data, kernel, this._dimensions, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
    {
        var result = await this._client.GetEmbeddingsAsync(this._client.ModelId, values.ToList(), kernel: null, this._dimensions, cancellationToken).ConfigureAwait(false);
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
            serviceKey is null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
