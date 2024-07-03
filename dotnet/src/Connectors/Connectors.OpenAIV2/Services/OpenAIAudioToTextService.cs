// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Services;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text-to-audio service.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAIAudioToTextService : IAudioToTextService
{
    /// <summary>
    /// OpenAI text-to-audio client for HTTP operations.
    /// </summary>
    private readonly ClientCore _client;

    /// <summary>
    /// Gets the attribute name used to store the organization in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string OrganizationKey => "Organization";

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Creates an instance of the <see cref="OpenAITextToAudioService"/> with API key auth.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="endpoint">Non-default endpoint for the OpenAI API.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIAudioToTextService(
        string modelId,
        string apiKey,
        string? organization = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId, nameof(modelId));
        this._client = new(modelId, apiKey, organization, endpoint, httpClient, loggerFactory?.CreateLogger(typeof(OpenAITextToAudioService)));
    }

    /// <summary>
    /// Creates an instance of the <see cref="OpenAITextToAudioService"/> with API key auth.
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
    {
        this._client.LogActionDetails();
        return this._client.GetTextFromAudioContentsAsync(content, executionSettings, cancellationToken);
    }
}
