// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI audio-to-text service.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class OpenAIAudioToTextService : IAudioToTextService
{
    /// <summary>Core implementation shared by OpenAI services.</summary>
    private readonly OpenAIClientCore _core;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <summary>
    /// Creates an instance of the <see cref="OpenAIAudioToTextService"/> with API key auth.
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
        this._core = new(
            modelId: modelId,
            apiKey: apiKey,
            organization: organization,
            httpClient: httpClient,
            logger: loggerFactory?.CreateLogger(typeof(OpenAIAudioToTextService)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        this._core.AddAttribute(OpenAIClientCore.OrganizationKey, organization);
    }

    /// <summary>
    /// Creates an instance of the <see cref="OpenAIAudioToTextService"/> using the specified <see cref="OpenAIClient"/>.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIAudioToTextService(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        this._core = new(modelId, openAIClient, loggerFactory?.CreateLogger(typeof(OpenAIAudioToTextService)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Creates an instance of the <see cref="OpenAIAudioToTextService"/> for Custom Audio OpenAI API
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="endpoint">Custom OpenAI Audio Transcription API compatible endpoint</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIAudioToTextService(
        string modelId,
        Uri endpoint,
        string? apiKey = default,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Uri? internalClientEndpoint = null;
        var providedEndpoint = endpoint ?? httpClient?.BaseAddress;
        if (providedEndpoint is not null)
        {
            // If the provided endpoint does not have a path specified, updates it to the default Message API Chat Completions endpoint
            internalClientEndpoint = providedEndpoint.PathAndQuery == "/" ?
                new Uri(providedEndpoint, "v1/audio/transcriptions")
                : providedEndpoint;
        }

        this._core = new(
            modelId: modelId,
            apiKey: apiKey,
            endpoint: internalClientEndpoint,
            organization: organization,
            httpClient: httpClient,
            logger: loggerFactory?.CreateLogger(typeof(OpenAIChatCompletionService)));

        if (providedEndpoint is not null)
        {
            this._core.AddAttribute(AIServiceExtensions.EndpointKey, providedEndpoint.ToString());
        }

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        this._core.AddAttribute(OpenAIClientCore.OrganizationKey, organization);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._core.GetTextContentFromAudioAsync(content, executionSettings, cancellationToken);
}
