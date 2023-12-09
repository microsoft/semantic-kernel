// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text embedding service.
/// </summary>
[Experimental("SKEXP0011")]
public sealed class OpenAITextEmbeddingGeneration : ITextEmbeddingGeneration
{
    private readonly OpenAIClientCore _core;

    /// <summary>
    /// Create an instance of the OpenAI text embedding connector
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextEmbeddingGeneration(
        OpenAIServiceConfig serviceConfig,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.ModelId);
        Verify.NotNullOrWhiteSpace(serviceConfig.ApiKey);

        this._core = new(serviceConfig.ModelId, serviceConfig.ApiKey, serviceConfig.Organization, httpClient, loggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGeneration)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <summary>
    /// Create an instance of the OpenAI text embedding connector
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextEmbeddingGeneration(
        OpenAIServiceConfig serviceConfig,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.ModelId);

        this._core = new(serviceConfig.ModelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGeneration)));
        this._core.SetAttributes(serviceConfig);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._core.LogActionDetails();
        return this._core.GetEmbeddingsAsync(data, kernel, cancellationToken);
    }
}
