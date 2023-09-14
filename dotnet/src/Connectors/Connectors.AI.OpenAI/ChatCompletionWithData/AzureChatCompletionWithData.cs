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
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/// <summary>
/// Azure OpenAI Chat Completion with data client.
/// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
/// </summary>
public sealed class AzureChatCompletionWithData : IChatCompletion, ITextCompletion
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureChatCompletionWithData"/> class.
    /// </summary>
    /// <param name="config">Instance of <see cref="AzureChatCompletionWithDataConfig"/> class with completion configuration.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">Instance of <see cref="ILoggerFactory"/> to use for logging.</param>
    public AzureChatCompletionWithData(
        AzureChatCompletionWithDataConfig config,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this.ValidateConfig(config);

        this._config = config;

        this._httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        return new OpenAIChatHistory(instructions);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        OpenAIChatRequestSettings chatRequestSettings = OpenAIRequestSettings.FromRequestSettings<OpenAIChatRequestSettings>(requestSettings);

        ValidateMaxTokens(chatRequestSettings.MaxTokens);

        return await this.ExecuteCompletionRequestAsync(chat, chatRequestSettings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        OpenAIChatRequestSettings chatRequestSettings = OpenAIRequestSettings.FromRequestSettings<OpenAIChatRequestSettings>(requestSettings);

        ValidateMaxTokens(chatRequestSettings.MaxTokens);

        return this.ExecuteCompletionStreamingRequestAsync(chat, chatRequestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        dynamic? requestSettings,
        CancellationToken cancellationToken = default)
    {
        OpenAIChatRequestSettings chatRequestSettings = OpenAIRequestSettings.FromRequestSettings<OpenAIChatRequestSettings>(requestSettings);

        var chat = this.PrepareChatHistory(text, requestSettings);

        return (await this.GetChatCompletionsAsync(chat, chatRequestSettings, cancellationToken).ConfigureAwait(false))
            .OfType<ITextResult>()
            .ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        dynamic? requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIChatRequestSettings chatRequestSettings = OpenAIRequestSettings.FromRequestSettings<OpenAIChatRequestSettings>(requestSettings);

        var chat = this.PrepareChatHistory(text, requestSettings);

        IAsyncEnumerable<IChatStreamingResult> results = this.GetStreamingChatCompletionsAsync(chat, chatRequestSettings, cancellationToken);
        await foreach (var result in results)
        {
            yield return (ITextStreamingResult)result;
        }
    }

    #region private ================================================================================

    private const string DefaultApiVersion = "2023-06-01-preview";

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
            throw new SKException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private async Task<IReadOnlyList<IChatResult>> ExecuteCompletionRequestAsync(
        ChatHistory chat,
        OpenAIChatRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        using var request = this.GetRequest(chat, requestSettings, isStreamEnabled: false);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var chatWithDataResponse = this.DeserializeResponse<ChatWithDataResponse>(body);

        return chatWithDataResponse.Choices.Select(choice => new ChatWithDataResult(chatWithDataResponse, choice)).ToList();
    }

    private async IAsyncEnumerable<IChatStreamingResult> ExecuteCompletionStreamingRequestAsync(
        ChatHistory chat,
        OpenAIChatRequestSettings requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var request = this.GetRequest(chat, requestSettings, isStreamEnabled: true);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);

        await foreach (var result in this.GetStreamingResultsAsync(response))
        {
            yield return result;
        }
    }

    private async Task<HttpResponseMessage> SendRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        request.Headers.Add("User-Agent", Telemetry.HttpUserAgent);
        request.Headers.Add("Api-Key", this._config.CompletionApiKey);

        try
        {
            return await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
            this._logger.LogError(
                "Error occurred on chat completion with data request execution: {ExceptionMessage}", ex.Message);

            throw;
        }
    }

    private async IAsyncEnumerable<IChatStreamingResult> GetStreamingResultsAsync(HttpResponseMessage response)
    {
        const string ServerEventPayloadPrefix = "data:";

        using var stream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
        using var reader = new StreamReader(stream);

        while (!reader.EndOfStream)
        {
            var body = await reader.ReadLineAsync().ConfigureAwait(false);

            if (string.IsNullOrWhiteSpace(body))
            {
                continue;
            }

            if (body.StartsWith(ServerEventPayloadPrefix, StringComparison.Ordinal))
            {
                body = body.Substring(ServerEventPayloadPrefix.Length);
            }

            var chatWithDataResponse = this.DeserializeResponse<ChatWithDataStreamingResponse>(body);

            foreach (var choice in chatWithDataResponse.Choices)
            {
                yield return new ChatWithDataStreamingResult(chatWithDataResponse, choice);
            }
        }
    }

    private T DeserializeResponse<T>(string body)
    {
        var response = Json.Deserialize<T>(body);

        if (response is null)
        {
            const string errorMessage = "Error occurred on chat completion with data response deserialization";

            this._logger.LogError(errorMessage);

            throw new SKException(errorMessage);
        }

        return response;
    }

    private HttpRequestMessage GetRequest(
        ChatHistory chat,
        OpenAIChatRequestSettings requestSettings,
        bool isStreamEnabled)
    {
        var payload = new ChatWithDataRequest
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

        return HttpRequest.CreatePostRequest(this.GetRequestUri(), payload);
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

    private ChatHistory PrepareChatHistory(string text, dynamic requestSettings)
    {
        var chat = this.CreateNewChat(requestSettings.ChatSystemPrompt);

        chat.AddUserMessage(text);

        return chat;
    }

    private string GetRequestUri()
    {
        const string EndpointUriFormat = "{0}/openai/deployments/{1}/extensions/chat/completions?api-version={2}";

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
