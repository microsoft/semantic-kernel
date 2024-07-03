// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.TextToImage;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// OpenAI text to image service.
/// </summary>
[Experimental("SKEXP0010")]
public class AzureOpenAITextToImageService : ITextToImageService
{
    private readonly ClientCore _client;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="modelId">The model to use for image generation.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organizationId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="endpoint">Non-default endpoint for the OpenAI API.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextToImageService(
        string modelId,
        string? apiKey = null,
        string? organizationId = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(modelId, apiKey, organizationId, endpoint, httpClient, loggerFactory?.CreateLogger(this.GetType()));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextToImageService(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(modelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGenerationService)));
    }

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        this._client.LogActionDetails();
        return this._client.GenerateImageAsync(description, width, height, cancellationToken);
    }
}
