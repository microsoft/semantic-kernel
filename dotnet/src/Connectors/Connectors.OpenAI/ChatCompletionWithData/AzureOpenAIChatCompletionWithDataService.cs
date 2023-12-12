// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.Text;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI Chat Completion with data service.
/// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIChatCompletionWithDataService : IChatCompletionService, ITextGenerationService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatCompletionWithDataService"/> class.
    /// </summary>
    /// <param name="config">Instance of <see cref="AzureOpenAIChatCompletionWithDataConfig"/> class with completion configuration.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">Instance of <see cref="ILoggerFactory"/> to use for logging.</param>
    public AzureOpenAIChatCompletionWithDataService(
        AzureOpenAIChatCompletionWithDataConfig config,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this.ValidateConfig(config);

        this._config = config;

        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
        this._attributes.Add(AIServiceExtensions.ModelIdKey, config.CompletionModelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.InternalGetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.InternalGetChatStreamingContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        return (await this.GetChatMessageContentsAsync(prompt, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
            .Select(chat => new TextContent(chat.Content, chat.ModelId, chat, Encoding.UTF8, chat.Metadata))
            .ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var streamingChatContent in this.InternalGetChatStreamingContentsAsync(new ChatHistory(prompt), executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(streamingChatContent.Content, streamingChatContent.ChoiceIndex, streamingChatContent.ModelId, streamingChatContent, Encoding.UTF8, streamingChatContent.Metadata);
        }
    }

    #region private ================================================================================

    private const string DefaultApiVersion = "2023-06-01-preview";

    private readonly AzureOpenAIChatCompletionWithDataConfig _config;

    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly Dictionary<string, object?> _attributes = new();
    private void ValidateConfig(AzureOpenAIChatCompletionWithDataConfig config)
    {
        Verify.NotNull(config);

        Verify.NotNullOrWhiteSpace(config.CompletionModelId);
        Verify.NotNullOrWhiteSpace(config.CompletionEndpoint);
        Verify.NotNullOrWhiteSpace(config.CompletionApiKey);
        Verify.NotNullOrWhiteSpace(config.DataSourceEndpoint);
        Verify.NotNullOrWhiteSpace(config.DataSourceApiKey);
        Verify.NotNullOrWhiteSpace(config.DataSourceIndex);
    }

    private async Task<IReadOnlyList<ChatMessageContent>> InternalGetChatMessageContentsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        var openAIExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettingsWithData(executionSettings, OpenAIPromptExecutionSettings.DefaultTextMaxTokens);

        using var request = this.GetRequest(chat, openAIExecutionSettings, isStreamEnabled: false);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var chatWithDataResponse = this.DeserializeResponse<ChatWithDataResponse>(body);
        var metadata = GetResponseMetadata(chatWithDataResponse);

        return chatWithDataResponse.Choices.Select(choice => new AzureOpenAIWithDataChatMessageContent(choice, this.GetModelId(), metadata)).ToList();
    }

    private static Dictionary<string, object?> GetResponseMetadata(ChatWithDataResponse chatResponse)
    {
        return new Dictionary<string, object?>(5)
        {
            { nameof(chatResponse.Id), chatResponse.Id },
            { nameof(chatResponse.Model), chatResponse.Model },
            { nameof(chatResponse.Created), chatResponse.Created },
            { nameof(chatResponse.Object), chatResponse.Object },
            { nameof(chatResponse.Usage), chatResponse.Usage },
        };
    }

    private static Dictionary<string, object?> GetResponseMetadata(ChatWithDataStreamingResponse chatResponse)
    {
        return new Dictionary<string, object?>(4)
        {
            { nameof(chatResponse.Id), chatResponse.Id },
            { nameof(chatResponse.Model), chatResponse.Model },
            { nameof(chatResponse.Created), chatResponse.Created },
            { nameof(chatResponse.Object), chatResponse.Object },
        };
    }

    private async Task<HttpResponseMessage> SendRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
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

    private async IAsyncEnumerable<AzureOpenAIWithDataStreamingChatMessageContent> InternalGetChatStreamingContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatRequestSettings = OpenAIPromptExecutionSettings.FromExecutionSettingsWithData(executionSettings);

        using var request = this.GetRequest(chatHistory, chatRequestSettings, isStreamEnabled: true);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);

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
            var metadata = GetResponseMetadata(chatWithDataResponse);

            foreach (var choice in chatWithDataResponse.Choices)
            {
                yield return new AzureOpenAIWithDataStreamingChatMessageContent(choice, choice.Index, this.GetModelId()!, new Dictionary<string, object?>(metadata));
            }
        }
    }

    private T DeserializeResponse<T>(string body)
    {
        var response = JsonSerializer.Deserialize<T>(body, JsonOptionsCache.ReadPermissive);

        if (response is null)
        {
            const string ErrorMessage = "Error occurred on chat completion with data response deserialization";

            this._logger.LogError(ErrorMessage);

            throw new KernelException(ErrorMessage);
        }

        return response;
    }

    private HttpRequestMessage GetRequest(
        ChatHistory chat,
        OpenAIPromptExecutionSettings executionSettings,
        bool isStreamEnabled)
    {
        var payload = new ChatWithDataRequest
        {
            Temperature = executionSettings.Temperature,
            TopP = executionSettings.TopP,
            IsStreamEnabled = isStreamEnabled,
            StopSequences = executionSettings.StopSequences,
            MaxTokens = executionSettings.MaxTokens,
            PresencePenalty = executionSettings.PresencePenalty,
            FrequencyPenalty = executionSettings.FrequencyPenalty,
            TokenSelectionBiases = executionSettings.TokenSelectionBiases ?? new Dictionary<int, int>(),
            DataSources = this.GetDataSources(),
            Messages = this.GetMessages(chat)
        };

        return HttpRequest.CreatePostRequest(this.GetRequestUri(), payload);
    }

    private List<ChatWithDataSource> GetDataSources()
    {
        return new List<ChatWithDataSource>
        {
            new() {
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
        // The system role as the unique message is not allowed in the With Data APIs.
        // This avoids the error: Invalid message request body. Learn how to use Completions extension API, please refer to https://learn.microsoft.com/azure/ai-services/openai/reference#completions-extensions
        if (chat.Count == 1 && chat[0].Role == AuthorRole.System)
        {
            // Converts a system message to a user message if is the unique message in the chat.
            chat[0].Role = AuthorRole.User;
        }

        return chat
            .Select(message => new ChatWithDataMessage
            {
                Role = message.Role.Label,
                Content = message.Content ?? string.Empty
            })
            .ToList();
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
