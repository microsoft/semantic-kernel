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
/// Azure OpenAI text-to-audio client for HTTP operations.
/// </summary>
[Experimental("SKEXP0005")]
internal sealed class AzureOpenAITextToAudioClient
{
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;

    private readonly string _deploymentName;
    private readonly string _endpoint;
    private readonly string _apiKey;
    private readonly string? _modelId;

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = new();

    /// <summary>
    /// Creates an instance of the <see cref="AzureOpenAITextToAudioClient"/> with API key auth.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureOpenAITextToAudioClient(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        Verify.NotNullOrWhiteSpace(apiKey);

        this._deploymentName = deploymentName;
        this._endpoint = endpoint;
        this._apiKey = apiKey;
        this._modelId = modelId;

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

        var modelId = this.GetModelId(audioExecutionSettings);

        using var request = this.GetRequest(text, modelId, audioExecutionSettings);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);
        using var stream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);

        var binaryData = await BinaryData.FromStreamAsync(stream, cancellationToken).ConfigureAwait(false);

        return new AudioContent(binaryData, modelId);
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
        request.Headers.Add("Api-Key", this._apiKey);

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

    private HttpRequestMessage GetRequest(string text, string modelId, OpenAITextToAudioExecutionSettings executionSettings)
    {
        const string DefaultApiVersion = "2024-02-15-preview";

        var baseUrl = !string.IsNullOrWhiteSpace(this._httpClient.BaseAddress?.AbsoluteUri) ?
            this._httpClient.BaseAddress!.AbsoluteUri :
            this._endpoint;

        var requestUrl = $"openai/deployments/{this._deploymentName}/audio/speech?api-version={DefaultApiVersion}";

        var payload = new TextToAudioRequest(modelId, text, executionSettings.Voice)
        {
            ResponseFormat = executionSettings.ResponseFormat,
            Speed = executionSettings.Speed
        };

        return HttpRequest.CreatePostRequest($"{baseUrl.TrimEnd('/')}/{requestUrl}", payload);
    }

    private string GetModelId(OpenAITextToAudioExecutionSettings executionSettings)
    {
        return
            !string.IsNullOrWhiteSpace(this._modelId) ? this._modelId! :
            !string.IsNullOrWhiteSpace(executionSettings.ModelId) ? executionSettings.ModelId! :
            this._deploymentName;
    }

    #endregion
}
