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
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextToAudio;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI text-to-audio service.
/// </summary>
[Experimental("SKEXP0005")]
public sealed class AzureOpenAITextToAudioService : ITextToAudioService
{
    private const string DefaultApiVersion = "2024-02-15-preview";

    private readonly Dictionary<string, object?> _attributes = new();
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;

    private readonly string _deploymentName;
    private readonly string _endpoint;
    private readonly string _apiKey;
    private readonly string? _modelId;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Gets the key used to store the deployment name in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string DeploymentNameKey => "DeploymentName";

    /// <summary>
    /// Creates an instance of the <see cref="AzureOpenAITextToAudioService"/> connector with API key auth.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextToAudioService(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
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
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;

        this.AddAttribute(DeploymentNameKey, deploymentName);
        this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public Task<AudioContent> GetAudioContentAsync(string text, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.InternalGetAudioContentAsync(text, executionSettings, cancellationToken);

    #region private

    private async Task<AudioContent> InternalGetAudioContentAsync(string text, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
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

    private async Task<HttpResponseMessage> SendRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
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
        var requestUrl = $"{this._endpoint.TrimEnd('/')}/openai/deployments/{this._deploymentName}/audio/speech?api-version={DefaultApiVersion}";

        var payload = new TextToAudioRequest(modelId, text, executionSettings.Voice)
        {
            ResponseFormat = executionSettings.ResponseFormat,
            Speed = executionSettings.Speed
        };

        return HttpRequest.CreatePostRequest(requestUrl, payload);
    }

    private string GetModelId(OpenAITextToAudioExecutionSettings executionSettings)
    {
        return
            !string.IsNullOrWhiteSpace(this._modelId) ? this._modelId! :
            !string.IsNullOrWhiteSpace(executionSettings.ModelId) ? executionSettings.ModelId! :
            this._deploymentName;
    }

    private void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this._attributes.Add(key, value);
        }
    }

    #endregion
}
