// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Contents;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text-to-audio client for HTTP operations.
/// </summary>
[Experimental("SKEXP0005")]
internal sealed class OpenAITextToAudioClient
{
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;

    private readonly string _modelId;
    private readonly string _apiKey;
    private readonly string? _organization;

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = new();

    /// <summary>
    /// Creates an instance of the <see cref="OpenAITextToAudioClient"/> with API key auth.
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal OpenAITextToAudioClient(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._modelId = modelId;
        this._apiKey = apiKey;
        this._organization = organization;

        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._logger = logger ?? NullLogger.Instance;
    }

    internal async Task<AudioContent> GetAudioContentAsync(
        string text,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        OpenAITextToAudioExecutionSettings? audioExecutionSettings = OpenAITextToAudioExecutionSettings.FromExecutionSettings(executionSettings);

        Verify.NotNullOrWhiteSpace(audioExecutionSettings?.Voice);

        using var request = this.GetRequest(text, audioExecutionSettings);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);
        using var stream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);

        var binaryData = await BinaryData.FromStreamAsync(stream, cancellationToken).ConfigureAwait(false);

        return new AudioContent(binaryData, this._modelId);
    }

    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

    #region private

    private async Task<HttpResponseMessage> SendRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        request.Headers.Add("Authorization", $"Bearer {this._apiKey}");

        if (!string.IsNullOrWhiteSpace(this._organization))
        {
            request.Headers.Add("OpenAI-Organization", this._organization);
        }

        try
        {
            return await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
            this._logger.LogError(
                "Error occurred on text-to-audio request execution: {ExceptionMessage}", ex.Message);

            throw;
        }
    }

    private HttpRequestMessage GetRequest(string text, OpenAITextToAudioExecutionSettings executionSettings)
    {
        const string DefaultBaseUrl = "https://api.openai.com";

        var baseUrl = !string.IsNullOrWhiteSpace(this._httpClient.BaseAddress?.AbsoluteUri) ?
            this._httpClient.BaseAddress!.AbsoluteUri :
            DefaultBaseUrl;

        var payload = new TextToAudioRequest(this._modelId, text, executionSettings.Voice)
        {
            ResponseFormat = executionSettings.ResponseFormat,
            Speed = executionSettings.Speed
        };

        return HttpRequest.CreatePostRequest($"{baseUrl.TrimEnd('/')}/v1/audio/speech", payload);
    }

    #endregion
}
