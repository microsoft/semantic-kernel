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

/* Phase 02
- Breaking the current constructor parameter order to follow the same order as the other services.
- Added custom endpoint support, and removed ApiKey validation, as it is performed by the ClientCore when the Endpoint is not provided.
- Added custom OpenAIClient support.
- Updated "organization" parameter to "organizationId".
- "modelId" parameter is now required in the constructor.

- Added OpenAIClient breaking glass constructor.
*/

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text to image service.
/// </summary>
[Experimental("SKEXP0010")]
public class OpenAITextToImageService : ITextToImageService
{
    private readonly ClientCore _client;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="modelId">The model to use for image generation.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organizationId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="endpoint">Non-default endpoint for the OpenAI API.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextToImageService(
        string modelId,
        string? apiKey = null,
        string? organizationId = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId, nameof(modelId));
        this._client = new(modelId, apiKey, organizationId, endpoint, httpClient, loggerFactory?.CreateLogger(this.GetType()));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextToImageService(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId, nameof(modelId));
        this._client = new(modelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAITextToImageService)));
    }

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        this._client.LogActionDetails();
        return this._client.GenerateImageAsync(description, width, height, cancellationToken);
    }
}
