// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents a client for interacting with the Anthropic chat completion models.
/// </summary>
internal sealed class AnthropicClient
{
    private const string ModelProvider = "anthropic";
    private readonly Func<ValueTask<string>>? _bearerTokenProvider;
    private readonly Dictionary<string, object?> _attributesInternal = new();

    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly string _modelId;
    private readonly string? _apiKey;
    private readonly Uri _endpoint;
    private readonly string? _version;

    private static readonly string s_namespace = typeof(AnthropicChatCompletionService).Namespace!;

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    private static readonly Meter s_meter = new(s_namespace);

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    private static readonly Counter<int> s_promptTokensCounter =
        s_meter.CreateCounter<int>(
            name: $"{s_namespace}.tokens.prompt",
            unit: "{token}",
            description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    private static readonly Counter<int> s_completionTokensCounter =
        s_meter.CreateCounter<int>(
            name: $"{s_namespace}.tokens.completion",
            unit: "{token}",
            description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    private static readonly Counter<int> s_totalTokensCounter =
        s_meter.CreateCounter<int>(
            name: $"{s_namespace}.tokens.total",
            unit: "{token}",
            description: "Number of tokens used");

    internal IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <summary>
    /// Represents a client for interacting with the Anthropic chat completion models.
    /// </summary>
    /// <param name="modelId">Model identifier</param>
    /// <param name="apiKey">ApiKey for the client</param>
    /// <param name="options">Options for the client</param>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    internal AnthropicClient(
        string modelId,
        string apiKey,
        AnthropicClientOptions options,
        HttpClient httpClient,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(options);
        Verify.NotNull(httpClient);

        Uri targetUri = httpClient.BaseAddress;
        if (httpClient.BaseAddress is null)
        {
            // If a custom endpoint is not provided, the ApiKey is required
            Verify.NotNullOrWhiteSpace(apiKey);
            this._apiKey = apiKey;
            targetUri = new Uri("https://api.anthropic.com/v1/messages");
        }

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._version = options.Version;
        this._endpoint = targetUri;

        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Represents a client for interacting with the Anthropic chat completion models.
    /// </summary>
    /// <param name="modelId">Model identifier</param>
    /// <param name="endpoint">Endpoint for the client</param>
    /// <param name="bearerTokenProvider">Bearer token provider</param>
    /// <param name="options">Options for the client</param>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    internal AnthropicClient(
        string modelId,
        Uri? endpoint,
        Func<ValueTask<string>> bearerTokenProvider,
        ClientOptions options,
        HttpClient httpClient,
        ILogger? logger = null)
    {
        this._version = options.Version;

        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(bearerTokenProvider);
        Verify.NotNull(options);
        Verify.NotNull(httpClient);

        Uri targetUri = endpoint ?? httpClient.BaseAddress
            ?? throw new ArgumentException("Endpoint is required if HttpClient.BaseAddress is not set.");

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._bearerTokenProvider = bearerTokenProvider;
        this._modelId = modelId;
        this._version = options?.Version;
        this._endpoint = targetUri;
    }

    /// <summary>
    /// Generates a chat message asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>Returns a list of chat message contents.</returns>
    internal async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var state = this.ValidateInputAndCreateChatCompletionState(chatHistory, executionSettings);

        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._endpoint, this._modelId, ModelProvider, chatHistory, state.ExecutionSettings);

        List<AnthropicChatMessageContent> chatResponses;
        AnthropicResponse anthropicResponse;
        try
        {
            anthropicResponse = await this.SendRequestAndReturnValidResponseAsync(
                    this._endpoint,
                    state.AnthropicRequest,
                    cancellationToken)
                .ConfigureAwait(false);

            chatResponses = this.GetChatResponseFrom(anthropicResponse);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        activity?.SetCompletionResponse(
            chatResponses,
            anthropicResponse.Usage?.InputTokens,
            anthropicResponse.Usage?.OutputTokens);

        return chatResponses;
    }

    private List<AnthropicChatMessageContent> GetChatResponseFrom(AnthropicResponse response)
    {
        var chatMessageContents = this.GetChatMessageContentsFromResponse(response);
        this.LogUsage(chatMessageContents);
        return chatMessageContents;
    }

    private void LogUsage(List<AnthropicChatMessageContent> chatMessageContents)
    {
        if (chatMessageContents[0].Metadata is not { TotalTokenCount: > 0 } metadata)
        {
            this.Log(LogLevel.Debug, "Token usage information unavailable.");
            return;
        }

        this.Log(LogLevel.Information,
            "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}. Total tokens: {TotalTokens}.",
            metadata.InputTokenCount,
            metadata.OutputTokenCount,
            metadata.TotalTokenCount);

        if (metadata.InputTokenCount.HasValue)
        {
            s_promptTokensCounter.Add(metadata.InputTokenCount.Value);
        }

        if (metadata.OutputTokenCount.HasValue)
        {
            s_completionTokensCounter.Add(metadata.OutputTokenCount.Value);
        }

        if (metadata.TotalTokenCount.HasValue)
        {
            s_totalTokensCounter.Add(metadata.TotalTokenCount.Value);
        }
    }

    private List<AnthropicChatMessageContent> GetChatMessageContentsFromResponse(AnthropicResponse response)
        => response.Contents.Select(content => this.GetChatMessageContentFromAnthropicContent(response, content)).ToList();

    private AnthropicChatMessageContent GetChatMessageContentFromAnthropicContent(AnthropicResponse response, AnthropicContent content)
    {
        if (!string.Equals(content.Type, "text", StringComparison.OrdinalIgnoreCase))
        {
            throw new NotSupportedException($"Content type {content.Type} is not supported yet.");
        }

        return new AnthropicChatMessageContent
        {
            Role = response.Role,
            Items = [new TextContent(content.Text ?? string.Empty)],
            ModelId = response.ModelId ?? this._modelId,
            InnerContent = response,
            Metadata = GetResponseMetadata(response)
        };
    }

    private static AnthropicMetadata GetResponseMetadata(AnthropicResponse response)
        => new()
        {
            MessageId = response.Id,
            FinishReason = response.StopReason,
            StopSequence = response.StopSequence,
            InputTokenCount = response.Usage?.InputTokens ?? 0,
            OutputTokenCount = response.Usage?.OutputTokens ?? 0
        };

    private async Task<AnthropicResponse> SendRequestAndReturnValidResponseAsync(
        Uri endpoint,
        AnthropicRequest anthropicRequest,
        CancellationToken cancellationToken)
    {
        using var httpRequestMessage = await this.CreateHttpRequestAsync(anthropicRequest, endpoint).ConfigureAwait(false);
        var body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
        var response = DeserializeResponse<AnthropicResponse>(body);
        return response;
    }

    private ChatCompletionState ValidateInputAndCreateChatCompletionState(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings)
    {
        ValidateChatHistory(chatHistory);

        var anthropicExecutionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ValidateMaxTokens(anthropicExecutionSettings.MaxTokens);
        anthropicExecutionSettings.ModelId ??= this._modelId;

        this.Log(LogLevel.Trace, "ChatHistory: {ChatHistory}, Settings: {Settings}",
            JsonSerializer.Serialize(chatHistory),
            JsonSerializer.Serialize(anthropicExecutionSettings));

        var filteredChatHistory = new ChatHistory(chatHistory.Where(IsAssistantOrUserOrSystem));
        var anthropicRequest = AnthropicRequest.FromChatHistoryAndExecutionSettings(filteredChatHistory, anthropicExecutionSettings);
        anthropicRequest.Version = this._version;

        return new ChatCompletionState
        {
            ChatHistory = chatHistory,
            ExecutionSettings = anthropicExecutionSettings,
            AnthropicRequest = anthropicRequest
        };

        static bool IsAssistantOrUserOrSystem(ChatMessageContent msg)
            => msg.Role == AuthorRole.Assistant || msg.Role == AuthorRole.User || msg.Role == AuthorRole.System;
    }

    /// <summary>
    /// Generates a stream of chat messages asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingChatMessageContent"/> streaming chat contents.</returns>
    internal async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        yield return new StreamingChatMessageContent(null, null);
        throw new NotImplementedException("Implement this method in next PR.");
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        // If maxTokens is null, it means that the user wants to use the default model value
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private static void ValidateChatHistory(ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);
        if (chatHistory.All(msg => msg.Role == AuthorRole.System))
        {
            throw new InvalidOperationException("Chat history can't contain only system messages.");
        }
    }

    private async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

    private async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    private static T DeserializeResponse<T>(string body)
    {
        try
        {
            return JsonSerializer.Deserialize<T>(body) ?? throw new JsonException("Response is null");
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    private async Task<HttpRequestMessage> CreateHttpRequestAsync(object requestData, Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        if (!httpRequestMessage.Headers.Contains("User-Agent"))
        {
            httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        }

        if (!httpRequestMessage.Headers.Contains(HttpHeaderConstant.Names.SemanticKernelVersion))
        {
            httpRequestMessage.Headers.Add(
                HttpHeaderConstant.Names.SemanticKernelVersion,
                HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AnthropicClient)));
        }

        if (!httpRequestMessage.Headers.Contains("anthropic-version"))
        {
            httpRequestMessage.Headers.Add("anthropic-version", this._version);
        }

        if (this._apiKey is not null && !httpRequestMessage.Headers.Contains("x-api-key"))
        {
            httpRequestMessage.Headers.Add("x-api-key", this._apiKey);
        }
        else
        if (this._bearerTokenProvider is not null && !httpRequestMessage.Headers.Contains("Authentication") && await this._bearerTokenProvider().ConfigureAwait(false) is { } bearerKey)
        {
            httpRequestMessage.Headers.Authorization = new AuthenticationHeaderValue("Bearer", bearerKey);
        }

        return httpRequestMessage;
    }

    private static HttpContent? CreateJsonContent(object? payload)
    {
        HttpContent? content = null;
        if (payload is not null)
        {
            byte[] utf8Bytes = payload is string s
                ? Encoding.UTF8.GetBytes(s)
                : JsonSerializer.SerializeToUtf8Bytes(payload);

            content = new ByteArrayContent(utf8Bytes);
            content.Headers.ContentType = new MediaTypeHeaderValue("application/json") { CharSet = "utf-8" };
        }

        return content;
    }

    private void Log(LogLevel logLevel, string? message, params object?[] args)
    {
        if (this._logger.IsEnabled(logLevel))
        {
#pragma warning disable CA2254 // Template should be a constant string.
            this._logger.Log(logLevel, message, args);
#pragma warning restore CA2254
        }
    }

    private sealed class ChatCompletionState
    {
        internal ChatHistory ChatHistory { get; set; } = null!;
        internal AnthropicRequest AnthropicRequest { get; set; } = null!;
        internal AnthropicPromptExecutionSettings ExecutionSettings { get; set; } = null!;
    }
}
