// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// Oobabooga chat completion service API.
/// Adapted from <see href="https://github.com/oobabooga/text-generation-webui/tree/main/api-examples"/>
/// </summary>
public sealed class OobaboogaChatCompletion : OobaboogaCompletionBase<ChatHistory, ChatRequestSettings, OobaboogaChatCompletionParameters, OobaboogaChatCompletionRequest, ChatCompletionResponse, ChatCompletionResult, ChatCompletionStreamingResult>, IChatCompletion, ITextCompletion
{
    private const string ChatBlockingUriPath = "/api/v1/chat";
    private const string ChatStreamingUriPath = "/api/v1/chat-stream";
    private const string ChatHistoryMustContainAtLeastOneUserMessage = "Chat history must contain at least one user message";

    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaChatCompletion"/> class.
    /// </summary>
    /// <param name="endpoint">The service API endpoint to which requests should be sent.</param>
    /// <param name="blockingPort">The port used for handling blocking requests. Default value is 5000</param>
    /// <param name="streamingPort">The port used for handling streaming requests. Default value is 5005</param>
    /// <param name="chatCompletionRequestSettings">An instance of <see cref="OobaboogaChatCompletionParameters"/>, which are chat completion settings specific to Oobabooga api</param>
    /// <param name="concurrentSemaphore">You can optionally set a hard limit on the max number of concurrent calls to the either of the completion methods by providing a <see cref="SemaphoreSlim"/>. Calls in excess will wait for existing consumers to release the semaphore</param>
    /// <param name="httpClient">Optional. The HTTP client used for making blocking API requests. If not specified, a default client will be used.</param>
    /// <param name="useWebSocketsPooling">If true, websocket clients will be recycled in a reusable pool as long as concurrent calls are detected</param>
    /// <param name="webSocketsCleanUpCancellationToken">if websocket pooling is enabled, you can provide an optional CancellationToken to properly dispose of the clean up tasks when disposing of the connector</param>
    /// <param name="keepAliveWebSocketsDuration">When pooling is enabled, pooled websockets are flushed on a regular basis when no more connections are made. This is the time to keep them in pool before flushing</param>
    /// <param name="webSocketFactory">The WebSocket factory used for making streaming API requests. Note that only when pooling is enabled will websocket be recycled and reused for the specified duration. Otherwise, a new websocket is created for each call and closed and disposed afterwards, to prevent data corruption from concurrent calls.</param>
    /// <param name="logger">Application logger</param>
    public OobaboogaChatCompletion(Uri endpoint, int blockingPort = 5000,
        int streamingPort = 5005,
        OobaboogaChatCompletionSettings? chatCompletionRequestSettings = null,
        SemaphoreSlim? concurrentSemaphore = null,
        HttpClient? httpClient = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = default,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        ILogger? logger = null) : base(endpoint, ChatBlockingUriPath, ChatStreamingUriPath, blockingPort, streamingPort, chatCompletionRequestSettings, concurrentSemaphore, httpClient, useWebSocketsPooling, webSocketsCleanUpCancellationToken, keepAliveWebSocketsDuration, webSocketFactory, logger)
    {
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        this.LogActionDetails();
        var toReturn = new ChatHistory();
        if (!string.IsNullOrWhiteSpace(instructions))
        {
            toReturn.AddSystemMessage(instructions!);
        }

        return toReturn;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return await this.InternalGetChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        await foreach (var chatCompletionStreamingResult in this.InternalGetStreamingChatCompletionsAsync(chat, requestSettings, cancellationToken))
        {
            yield return chatCompletionStreamingResult;
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        ChatHistory chat = this.PrepareChatHistory(text, requestSettings, out ChatRequestSettings chatSettings);
        return (await this.InternalGetChatCompletionsAsync(chat, chatSettings, cancellationToken).ConfigureAwait(false))
            .OfType<ITextResult>()
            .ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        ChatHistory chat = this.PrepareChatHistory(text, requestSettings, out ChatRequestSettings chatSettings);

        await foreach (var chatCompletionStreamingResult in this.InternalGetStreamingChatCompletionsAsync(chat, chatSettings, cancellationToken))
        {
            yield return (ITextStreamingResult)chatCompletionStreamingResult;
        }
    }

    #region private ================================================================================

   
    protected override CompletionStreamingResponseBase? GetResponseObject(string messageText)
    {
        return Json.Deserialize<ChatCompletionStreamingResponse>(messageText);
    }

    private async Task<IReadOnlyList<IChatResult>> InternalGetChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotEmptyList(chat, ChatHistoryMustContainAtLeastOneUserMessage, nameof(chat));
        return await this.GetCompletionsBaseAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<IChatStreamingResult> InternalGetStreamingChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotEmptyList(chat, ChatHistoryMustContainAtLeastOneUserMessage, nameof(chat));

        await foreach (var chatCompletionStreamingResult in this.GetStreamingCompletionsBaseAsync(chat, requestSettings, cancellationToken))
        {
            yield return chatCompletionStreamingResult;
        }
    }

    private ChatHistory PrepareChatHistory(string text, CompleteRequestSettings? requestSettings, out ChatRequestSettings settings)
    {
        requestSettings ??= new();
        var chat = this.CreateNewChat(requestSettings.ChatSystemPrompt);
        chat.AddUserMessage(text);
        settings = new ChatRequestSettings
        {
            MaxTokens = requestSettings.MaxTokens,
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            StopSequences = requestSettings.StopSequences,
            ResultsPerPrompt = requestSettings.ResultsPerPrompt,
            TokenSelectionBiases = requestSettings.TokenSelectionBiases,
        };
        return chat;
    }

    #endregion

    protected override IReadOnlyList<ChatCompletionResult> GetCompletionResults(ChatCompletionResponse completionResponse)
    {
        return completionResponse.Results.ConvertAll(result => new ChatCompletionResult(result));
    }

    protected override OobaboogaChatCompletionRequest CreateCompletionRequest(ChatHistory input, ChatRequestSettings? requestSettings)
    {
        requestSettings ??= new ChatRequestSettings();

        var completionRequest = OobaboogaChatCompletionRequest.Create(input, (OobaboogaCompletionSettings<OobaboogaChatCompletionParameters>)this.OobaboogaSettings, requestSettings);
        return completionRequest;
    }
}
