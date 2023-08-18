// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/// <summary>
/// Azure OpenAI Chat Completion with data client.
/// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
/// </summary>
public sealed class AzureChatCompletionWithData : IChatCompletion
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureChatCompletionWithData"/> class.
    /// </summary>
    /// <param name="config">Instance of <see cref="AzureChatCompletionWithDataConfig"/> class with completion configuration.</param>
    /// <param name="httpClient"></param>
    /// <param name="logger"></param>
    public AzureChatCompletionWithData(
        AzureChatCompletionWithDataConfig config,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        this.ValidateConfig(config);

        this._config = config;

        this._httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        return new OpenAIChatHistory(instructions);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        requestSettings ??= new();

        ValidateMaxTokens(requestSettings.MaxTokens);

        return await this.ExecuteCompletionRequestAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        requestSettings ??= new();

        ValidateMaxTokens(requestSettings.MaxTokens);

        return this.ExecuteCompletionStreamingRequestAsync(chat, requestSettings, cancellationToken);
    }

    #region private ================================================================================

    private const string ServerEventPayloadPrefix = "data:";
    private const string DefaultApiVersion = "2023-06-01-preview";
    private const string EndpointUriFormat = "{0}/openai/deployments/{1}/extensions/chat/completions?api-version={2}";

    private readonly AzureChatCompletionWithDataConfig _config;

    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;

    private void ValidateConfig(AzureChatCompletionWithDataConfig config)
    {
        Verify.NotNull(config);

        Verify.NotNullOrWhiteSpace(config.CompletionModelId);
        Verify.NotNullOrWhiteSpace(config.CompletionEndpoint);
        Verify.NotNullOrWhiteSpace(config.CompletionApiKey);
        Verify.NotNullOrWhiteSpace(config.DataSourceEndpoint);
        Verify.NotNullOrWhiteSpace(config.DataSourceApiKey);
        Verify.NotNullOrWhiteSpace(config.DataSourceIndex);
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens.HasValue && maxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private async Task<IReadOnlyList<IChatResult>> ExecuteCompletionRequestAsync(
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        var request = this.GetRequest(chat, requestSettings, isStreamEnabled: false);
        using var response = await this.GetResponse(request, cancellationToken).ConfigureAwait(false);

        this.EnsureSuccessStatusCode(response);

        var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        var chatWithDataResponse = this.DeserializeResponse<ChatWithDataResponse>(body);

        return chatWithDataResponse.Choices.Select(choice => new ChatWithDataResult(choice)).ToList();
    }

    private async IAsyncEnumerable<IChatStreamingResult> ExecuteCompletionStreamingRequestAsync(
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var request = this.GetRequest(chat, requestSettings, isStreamEnabled: true);
        using var response = await this.GetResponse(request, cancellationToken).ConfigureAwait(false);

        this.EnsureSuccessStatusCode(response);

        using var stream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
        using var reader = new StreamReader(stream);

        while (!reader.EndOfStream)
        {
            var body = await reader.ReadLineAsync().ConfigureAwait(false);

            if (body.StartsWith(ServerEventPayloadPrefix, StringComparison.OrdinalIgnoreCase))
            {
                body = body.Substring(ServerEventPayloadPrefix.Length);
            }

            if (body.Length == 0)
            {
                continue;
            }

            var chatWithDataResponse = this.DeserializeResponse<ChatWithDataStreamingResponse>(body);

            var choice = chatWithDataResponse.Choices.LastOrDefault();

            yield return new ChatWithDataStreamingResult(choice);
        }
    }

    private async Task<HttpResponseMessage> GetResponse(
        ChatWithDataRequest request,
        CancellationToken cancellationToken = default)
    {
        using var httpRequestMessage = HttpRequest.CreatePostRequest(this.GetRequestUri(), request);

        httpRequestMessage.Headers.Add("User-Agent", Telemetry.HttpUserAgent);
        httpRequestMessage.Headers.Add("Api-Key", this._config.CompletionApiKey);

        return await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    private void EnsureSuccessStatusCode(HttpResponseMessage response)
    {
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException ex)
        {
            this._logger.LogError(
                "Error occurred on chat completion with data request execution: {ExceptionMessage}", ex.Message);

            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Error occurred on chat completion with data request execution: {ex.Message}", ex);
        }
    }

    private T DeserializeResponse<T>(string body)
    {
        var response = Json.Deserialize<T>(body);

        if (response == null)
        {
            const string errorMessage = "Error occurred on chat completion with data response deserialization";

            this._logger.LogError(errorMessage);

            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                errorMessage);
        }

        return response;
    }

    private ChatWithDataRequest GetRequest(
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        bool isStreamEnabled)
    {
        return new ChatWithDataRequest
        {
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            IsStreamEnabled = isStreamEnabled,
            StopSequences = requestSettings.StopSequences,
            MaxTokens = requestSettings.MaxTokens,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            TokenSelectionBiases = requestSettings.TokenSelectionBiases,
            DataSources = this.GetDataSources(),
            Messages = this.GetMessages(chat)
        };
    }

    private List<ChatWithDataSource> GetDataSources()
    {
        return new List<ChatWithDataSource>
        {
            new ChatWithDataSource
            {
                Parameters = new ChatWithDataSourceParameters
                {
                    Endpoint = this._config.DataSourceEndpoint,
                    ApiKey = this._config.DataSourceApiKey,
                    IndexName = this._config.DataSourceIndex
                }
            }
        };
    }

    private List<ChatWithDataMessage> GetMessages(ChatHistory chat)
    {
        return chat
            .Select(message => new ChatWithDataMessage
            {
                Role = message.Role.Label,
                Content = message.Content
            })
            .ToList();
    }

    private string GetRequestUri()
    {
        var apiVersion = this._config.CompletionApiVersion;

        if (string.IsNullOrWhiteSpace(apiVersion))
        {
            apiVersion = DefaultApiVersion;
        }

        return string.Format(
            CultureInfo.InvariantCulture,
            EndpointUriFormat,
            this._config.CompletionEndpoint.TrimEnd('/'),
            this._config.CompletionModelId,
            apiVersion);
    }

    #endregion
}
