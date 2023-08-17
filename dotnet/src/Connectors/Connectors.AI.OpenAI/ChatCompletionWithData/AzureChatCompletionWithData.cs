// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

public sealed class AzureChatCompletionWithData : IChatCompletion
{
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

    public ChatHistory CreateNewChat(string? instructions = null)
    {
        return new OpenAIChatHistory(instructions);
    }

    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        requestSettings ??= new();

        ValidateMaxTokens(requestSettings.MaxTokens);

        return await this.ExecuteChatCompletionsRequestAsync(chat, requestSettings, isStreamEnabled: false, cancellationToken).ConfigureAwait(false);
    }

    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    #region private ================================================================================

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

    private async Task<IReadOnlyList<IChatResult>> ExecuteChatCompletionsRequestAsync(
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        bool isStreamEnabled,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var request = new ChatWithDataRequest
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

            using var httpRequestMessage = HttpRequest.CreatePostRequest(this.GetRequestUri(), request);

            httpRequestMessage.Headers.Add("User-Agent", Telemetry.HttpUserAgent);
            httpRequestMessage.Headers.Add("Api-Key", this._config.CompletionApiKey);

            using var response = await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var chatWithDataResponse = this.DeserializeResponse<ChatWithDataResponse>(body);

            return chatWithDataResponse.Choices.Select(choice => new ChatWithDataResult(choice)).ToList();
        }
        catch (Exception ex) when (ex is not AIException && !ex.IsCriticalException())
        {
            this._logger.LogError(ex,
                "Error occurred on chat completion with data request execution: {ExceptionMessage}", ex.Message);

            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Error occurred on chat completion with data request execution: {ex.Message}", ex);
        }
    }

    private T DeserializeResponse<T>(string body)
    {
        var response = JsonSerializer.Deserialize<T>(body);

        if (response == null)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                "Error occurred on chat completion with data response deserialization");
        }

        return response;
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
