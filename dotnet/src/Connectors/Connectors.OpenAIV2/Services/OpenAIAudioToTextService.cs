// Copyright (c) Microsoft. All rights reserved.

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
    /// <param name="config">Service configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public OpenAIAudioToTextService(
        OpenAIClientAudioToTextServiceConfig config,
        HttpClient? httpClient = null)
    {
        this._core = new(config, httpClient: httpClient);

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, config.ModelId);
        this._core.AddAttribute(OpenAIClientCore.OrganizationKey, config.OrganizationId);
    }

    /// <summary>
    /// Creates an instance of the <see cref="OpenAIAudioToTextService"/> using the specified <see cref="OpenAIClient"/>.
    /// </summary>
    /// <param name="config">Service configuration</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    public OpenAIAudioToTextService(
        OpenAIAudioToTextServiceConfig config,
        OpenAIClient openAIClient)
    {
        this._core = new(config, openAIClient);

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, config.ModelId);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._core.GetTextContentFromAudioAsync(content, executionSettings, cancellationToken);
}
