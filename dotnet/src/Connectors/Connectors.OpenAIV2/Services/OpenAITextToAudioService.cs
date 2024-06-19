// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextToAudio;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text-to-audio service.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class OpenAITextToAudioService : ITextToAudioService
{
    /// <summary>
    /// OpenAI text-to-audio client for HTTP operations.
    /// </summary>
    private readonly OpenAITextToAudioClient _client;

    /// <summary>
    /// Gets the attribute name used to store the organization in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string OrganizationKey => "Organization";

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Creates an instance of the <see cref="OpenAITextToAudioService"/> with API key auth.
    /// </summary>
    /// <param name="config">Service configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public OpenAITextToAudioService(
        OpenAIClientTextToAudioConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(config.ModelId);
        Verify.NotNull(config.ApiKey);

        this._client = new(config.ModelId!, config.ApiKey!, config.OrganizationId, httpClient, config.LoggerFactory?.CreateLogger(typeof(OpenAITextToAudioService)));

        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, config.ModelId);
        this._client.AddAttribute(OrganizationKey, config.OrganizationId);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<AudioContent>> GetAudioContentsAsync(
        string text,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetAudioContentsAsync(text, executionSettings, cancellationToken);
}
