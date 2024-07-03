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
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents a client for interacting with the Anthropic chat completion models.
/// </summary>
internal sealed class AnthropicClient
{
    private const string ModelProvider = "anthropic";

    internal static JsonSerializerOptions SerializerOptions { get; }
        = new(JsonOptionsCache.Default)
        {
            Converters = { new PolymorphicJsonConverterFactory() },
            TypeInfoResolver = JsonTypeDiscriminatorHelper.TypeInfoResolver
        };

    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly string _modelId;
    private readonly string? _apiKey;
    private readonly Uri _endpoint;
    private readonly Func<HttpRequestMessage, ValueTask>? _customRequestHandler;
    private readonly AnthropicClientOptions _options;

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

    /// <summary>
    /// Represents a client for interacting with the Anthropic chat completion models.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="apiKey">Api key</param>
    /// <param name="options">Options for the client</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public AnthropicClient(
        HttpClient httpClient,
        string modelId,
        string apiKey,
        AnthropicClientOptions? options,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._apiKey = apiKey;
        this._options = options ?? new AnthropicClientOptions();
        this._endpoint = new Uri("https://api.anthropic.com/v1/messages");
    }

    /// <summary>
    /// Represents a client for interacting with the Anthropic chat completion models.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="requestHandler">A custom request handler to be used for sending HTTP requests</param>
    /// <param name="options">Options for the client</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public AnthropicClient(
        HttpClient httpClient,
        string modelId,
        Uri endpoint,
        Func<HttpRequestMessage, ValueTask>? requestHandler,
        AnthropicClientOptions? options,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(endpoint);

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._endpoint = endpoint;
        this._customRequestHandler = requestHandler;
        this._options = options ?? new AnthropicClientOptions();
    }

    /// <summary>
    /// Generates a chat message asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>Returns a list of chat message contents.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
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
                this._endpoint, state.AnthropicRequest, cancellationToken).ConfigureAwait(false);
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

        s_promptTokensCounter.Add(metadata.InputTokenCount);
        s_completionTokensCounter.Add(metadata.OutputTokenCount);
        s_totalTokensCounter.Add(metadata.TotalTokenCount);
    }

    private List<AnthropicChatMessageContent> GetChatMessageContentsFromResponse(AnthropicResponse response)
        => response.Contents.Select(content => this.GetChatMessageContentFromAnthropicContent(response, content)).ToList();

    private AnthropicChatMessageContent GetChatMessageContentFromAnthropicContent(AnthropicResponse response, AnthropicContent content)
    {
        if (content is not AnthropicTextContent textContent)
        {
            throw new NotSupportedException($"Content type {content.GetType()} is not supported yet.");
        }

        return new AnthropicChatMessageContent(
            role: response.Role,
            items: [new TextContent(textContent.Text ?? string.Empty)],
            modelId: response.ModelId ?? this._modelId,
            innerContent: response,
            metadata: GetResponseMetadata(response));
    }

    private static AnthropicMetadata GetResponseMetadata(AnthropicResponse response)
        => new()
        {
            MessageId = response.Id,
            FinishReason = response.FinishReason,
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
        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var response = DeserializeResponse<AnthropicResponse>(body);
        ValidateAnthropicResponse(response);
        return response;
    }

    private static void ValidateAnthropicResponse(AnthropicResponse response)
    {
        if (response.Contents is null || response.Contents.Count == 0)
        {
            throw new KernelException("Anthropic API doesn't return any data.");
        }
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
        return new ChatCompletionState()
        {
            ChatHistory = chatHistory,
            ExecutionSettings = anthropicExecutionSettings,
            AnthropicRequest = AnthropicRequest.FromChatHistoryAndExecutionSettings(filteredChatHistory, anthropicExecutionSettings)
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
    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
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
            return JsonSerializer.Deserialize<T>(body, options: SerializerOptions) ?? throw new JsonException("Response is null");
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
        var httpRequestMessage = new HttpRequestMessage(HttpMethod.Post, endpoint) { Content = CreateJsonContent(requestData) };
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        httpRequestMessage.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AnthropicClient)));

        if (this._customRequestHandler != null)
        {
            await this._customRequestHandler(httpRequestMessage).ConfigureAwait(false);
        }
        else
        {
            httpRequestMessage.Headers.Add("anthropic-version", this._options.Version);
            httpRequestMessage.Headers.Add("x-api-key", this._apiKey);
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
                : JsonSerializer.SerializeToUtf8Bytes(payload, SerializerOptions);

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
