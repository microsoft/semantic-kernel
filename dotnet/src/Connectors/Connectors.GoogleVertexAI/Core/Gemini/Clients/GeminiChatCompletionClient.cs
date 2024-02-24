// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a client for interacting with the chat completion gemini model.
/// </summary>
internal class GeminiChatCompletionClient : GeminiClient, IGeminiChatCompletionClient
{
    private readonly IStreamJsonParser _streamJsonParser;
    private readonly string _modelId;

    /// <summary>
    /// The maximum number of auto-invokes that can be in-flight at any given time as part of the current
    /// asynchronous chain of execution.
    /// </summary>
    /// <remarks>
    /// This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
    /// auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
    /// we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
    /// to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
    /// With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
    /// execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
    /// prompt function could advertise itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    private const int MaxInflightAutoInvokes = 5;

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    private static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    /// <summary>
    /// Represents a client for interacting with the chat completion gemini model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this._modelId = modelId;
        this._streamJsonParser = streamJsonParser ?? new GeminiStreamJsonParser();
    }

    /// <inheritdoc/>
    public virtual async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var chatHistoryCopy = new ChatHistory(chatHistory);
        ValidateAndPrepareChatHistory(chatHistoryCopy);

        var endpoint = this.EndpointProvider.GetGeminiChatCompletionEndpoint(this._modelId);

        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(executionSettings);
        bool autoInvoke = CheckAutoInvokeCondition(kernel, geminiExecutionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);
        ValidateAutoInvoke(autoInvoke, geminiExecutionSettings.CandidateCount ?? 1);

        for (int iteration = 1;; iteration++)
        {
            var geminiRequest = CreateRequest(chatHistoryCopy, geminiExecutionSettings, kernel);
            var geminiResponse = await this.SendRequestAndReturnValidResponseAsync(endpoint, geminiRequest, cancellationToken)
                .ConfigureAwait(false);

            var chatMessagesContents = this.ProcessChatResponse(geminiResponse);

            // If we don't want to attempt to invoke any functions, just return the result.
            // Or if we are auto-invoking but we somehow end up with other than 1 choice even though only 1 was requested, similarly bail.
            if (!autoInvoke || geminiResponse.Candidates!.Count != 1)
            {
                return chatMessagesContents;
            }

            var responsePart = geminiResponse.Candidates[0].Content!.Parts[0];
            if (responsePart.FunctionCall is null)
            {
                return chatMessagesContents;
            }

            chatHistory.Add(chatMessagesContents[0]);
            chatHistoryCopy.Add(chatMessagesContents[0]);

            this.Logger.LogDebug("Tool requests: {Requests}", 1);
            this.Logger.LogTrace("Function call requests: {FunctionCall}", responsePart.FunctionCall.ToString());
        }
    }

    private async Task<GeminiResponse> SendRequestAndReturnValidResponseAsync(
        Uri endpoint,
        GeminiRequest geminiRequest,
        CancellationToken cancellationToken)
    {
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);
        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var geminiResponse = DeserializeResponse<GeminiResponse>(body);
        ValidateGeminiResponse(geminiResponse);
        return geminiResponse;
    }

    private static bool CheckAutoInvokeCondition(Kernel? kernel, GeminiPromptExecutionSettings geminiExecutionSettings)
    {
        return kernel is not null
               && geminiExecutionSettings.ToolCallBehavior?.MaximumAutoInvokeAttempts > 0
               && s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;
    }

    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ValidateAndPrepareChatHistory(ref chatHistory);

        var endpoint = this.EndpointProvider.GetGeminiStreamChatCompletionEndpoint(this._modelId);
        var geminiRequest = CreateRequest(chatHistory, executionSettings, kernel);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        foreach (var streamingChatMessageContent in this.ProcessChatResponseStream(responseStream))
        {
            yield return streamingChatMessageContent;
        }
    }

    private static void ValidateAndPrepareChatHistory(ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);

        if (chatHistory.Where(message => message.Role == AuthorRole.System).ToList() is { Count: > 0 } systemMessages)
        {
            if (chatHistory.Count == systemMessages.Count)
            {
                throw new InvalidOperationException("Chat history can't contain only system messages.");
            }

            if (systemMessages.Count > 1)
            {
                throw new InvalidOperationException("Chat history can't contain more than one system message. " +
                                                    "Only the first system message will be processed but will be converted to the user message before sending to the Gemini api.");
            }

            ConvertSystemMessageToUserMessageInChatHistory(chatHistory, systemMessages[0]);
        }

        ValidateChatHistoryMessagesOrder(chatHistory);
    }

    private static void ConvertSystemMessageToUserMessageInChatHistory(ChatHistory chatHistory, ChatMessageContent systemMessage)
    {
        // TODO: This solution is needed due to the fact that Gemini API doesn't support system messages. Maybe in the future we will be able to remove it.
        chatHistory.Remove(systemMessage);
        if (!string.IsNullOrWhiteSpace(systemMessage.Content))
        {
            chatHistory.Insert(0, new ChatMessageContent(AuthorRole.User, systemMessage.Content));
            chatHistory.Insert(1, new ChatMessageContent(AuthorRole.Assistant, "OK"));
        }
    }

    private static void ValidateChatHistoryMessagesOrder(ChatHistory chatHistory)
    {
        bool incorrectOrder = false;
        for (int i = 0; i < chatHistory.Count; i++)
        {
            if (chatHistory[i].Role != (i % 2 == 0 ? AuthorRole.User : AuthorRole.Assistant) ||
                (i == chatHistory.Count - 1 && chatHistory[i].Role != AuthorRole.User))
            {
                incorrectOrder = true;
                break;
            }
        }

        if (incorrectOrder)
        {
            throw new NotSupportedException(
                "Gemini API support only chat history with order of messages alternates between the user and the assistant. " +
                "Last message have to be User message.");
        }
    }

    private IEnumerable<StreamingChatMessageContent> ProcessChatResponseStream(Stream responseStream)
        => from geminiResponse in this.ParseResponseStream(responseStream)
           from chatMessageContent in this.ProcessChatResponse(geminiResponse)
           select GetStreamingChatContentFromChatContent(chatMessageContent);

    private IEnumerable<GeminiResponse> ParseResponseStream(Stream responseStream)
        => this._streamJsonParser.Parse(responseStream).Select(DeserializeResponse<GeminiResponse>);

    private List<GeminiChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
    {
        ValidateGeminiResponse(geminiResponse);

        var chatMessageContents = this.GetChatMessageContentsFromResponse(geminiResponse);
        this.LogUsage(chatMessageContents);
        return chatMessageContents;
    }

    private static void ValidateGeminiResponse(GeminiResponse geminiResponse)
    {
        if (geminiResponse.Candidates == null || !geminiResponse.Candidates.Any())
        {
            if (geminiResponse.PromptFeedback?.BlockReason != null)
            {
                // TODO: Currently SK doesn't support prompt feedback/finish status, so we just throw an exception. I told SK team that we need to support it: https://github.com/microsoft/semantic-kernel/issues/4621
                throw new KernelException("Prompt was blocked due to Gemini API safety reasons.");
            }

            throw new KernelException("Gemini API doesn't return any data.");
        }
    }

    private void LogUsage(IReadOnlyList<ChatMessageContent> chatMessageContents)
        => this.LogUsageMetadata((GeminiMetadata)chatMessageContents[0].Metadata!);

    private List<GeminiChatMessageContent> GetChatMessageContentsFromResponse(GeminiResponse geminiResponse)
        => geminiResponse.Candidates!.Select(candidate => this.GetChatMessageContentFromCandidate(geminiResponse, candidate)).ToList();

    private GeminiChatMessageContent GetChatMessageContentFromCandidate(GeminiResponse geminiResponse, GeminiResponseCandidate candidate)
    {
        return new GeminiChatMessageContent(
            role: candidate.Content?.Role ?? AuthorRole.Assistant,
            content: candidate.Content?.Parts[0].Text,
            modelId: this._modelId,
            metadata: GetResponseMetadata(geminiResponse, candidate));
    }

    private static GeminiRequest CreateRequest(
        ChatHistory chatHistory,
        GeminiPromptExecutionSettings geminiExecutionSettings,
        Kernel? kernel)
    {
        var geminiRequest = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, geminiExecutionSettings);
        geminiExecutionSettings.ToolCallBehavior?.ConfigureGeminiRequest(kernel, geminiRequest);
        return geminiRequest;
    }

    private static StreamingChatMessageContent GetStreamingChatContentFromChatContent(ChatMessageContent chatMessageContent)
        => new(
            role: chatMessageContent.Role,
            content: chatMessageContent.Content,
            modelId: chatMessageContent.ModelId,
            innerContent: chatMessageContent.InnerContent,
            metadata: chatMessageContent.Metadata,
            choiceIndex: ((GeminiMetadata)chatMessageContent.Metadata!).Index);

    private static void ValidateAutoInvoke(bool autoInvoke, int resultsPerPrompt)
    {
        if (autoInvoke && resultsPerPrompt != 1)
        {
            // We can remove this restriction in the future if valuable. However, multiple results per prompt is rare,
            // and limiting this significantly curtails the complexity of the implementation.
            throw new ArgumentException(
                $"Auto-invocation of tool calls may only be used with a {nameof(GeminiPromptExecutionSettings.CandidateCount)} of 1.");
        }
    }
}
