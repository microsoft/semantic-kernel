// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AudioToText;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI audio-to-text service.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAIAudioToTextService : IAudioToTextService
{
    /// <summary>
    /// OpenAI audio-to-text client for HTTP operations.
    /// </summary>
    private readonly ClientCore _client;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAudioToTextService"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIAudioToTextService(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId, nameof(modelId));
        this._client = new(modelId, apiKey, organization, null, httpClient, loggerFactory?.CreateLogger(typeof(OpenAIAudioToTextService)));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAudioToTextService"/> class for a custom OpenAI-compatible endpoint.
    /// </summary>
    /// <param name="modelId">Model name.</param>
    /// <param name="endpoint">OpenAI-compatible API endpoint.</param>
    /// <param name="apiKey">Optional API key.</param>
    /// <param name="organization">OpenAI Organization Id (usually optional).</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIAudioToTextService(
        string modelId,
        Uri endpoint,
        string? apiKey = null,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId, nameof(modelId));
        Verify.NotNull(endpoint);
        this._client = new(modelId, apiKey, organization, endpoint, httpClient, loggerFactory?.CreateLogger(typeof(OpenAIAudioToTextService)));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAudioToTextService"/> class.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIAudioToTextService(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId, nameof(modelId));
        this._client = new(modelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAITextToAudioService)));
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetTextFromAudioContentsAsync(this._client.ModelId, content, executionSettings, cancellationToken);
}
