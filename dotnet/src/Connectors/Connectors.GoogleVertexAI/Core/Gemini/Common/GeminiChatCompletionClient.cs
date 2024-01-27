// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
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
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        ValidateAndPrepareChatHistory(ref chatHistory);

        var endpoint = this.EndpointProvider.GetChatCompletionEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.ParseAndProcessChatResponse(body);
    }

    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ValidateAndPrepareChatHistory(ref chatHistory);

        var endpoint = this.EndpointProvider.GetStreamChatCompletionEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(chatHistory, executionSettings);
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

    private static void ValidateAndPrepareChatHistory(ref ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);

        if (chatHistory.Where(message => message.Role == AuthorRole.System).ToList() is { Count: > 0 } systemMessages)
        {
            if (chatHistory.Count == systemMessages.Count)
            {
                throw new KernelException("Chat history can't contain only system messages.");
            }

            chatHistory = PrepareChatHistoryWithSystemMessages(chatHistory, systemMessages);
        }

        ValidateChatHistoryMessagesOrder(chatHistory);
    }

    private static ChatHistory PrepareChatHistoryWithSystemMessages(ChatHistory chatHistory, IEnumerable<ChatMessageContent> systemMessages)
    {
        // TODO: This solution is needed due to the fact that Gemini API doesn't support system messages. Maybe in the future we will be able to remove it.
        chatHistory = new ChatHistory(chatHistory);
        var systemMessageBuilder = new StringBuilder();
        string separator = "\n-----\n";
        foreach (var message in systemMessages)
        {
            chatHistory.Remove(message);
            if (!string.IsNullOrWhiteSpace(message.Content))
            {
                systemMessageBuilder.Append(message.Content);
                systemMessageBuilder.Append(separator);
            }
        }

        if (systemMessageBuilder.Length > 0)
        {
            string content = systemMessageBuilder.ToString();
            content = content.Remove(content.LastIndexOf(separator, StringComparison.Ordinal));
            chatHistory.Insert(0, new ChatMessageContent(AuthorRole.User, content));
            chatHistory.Insert(1, new ChatMessageContent(AuthorRole.Assistant, "OK"));
        }

        return chatHistory;
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

    private List<ChatMessageContent> ParseAndProcessChatResponse(string body)
        => this.ProcessChatResponse(DeserializeResponse<GeminiResponse>(body));

    private List<ChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
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

        var chatMessageContents = this.GetChatMessageContentsFromResponse(geminiResponse);
        this.LogUsage(chatMessageContents);
        return chatMessageContents;
    }

    private void LogUsage(IReadOnlyList<ChatMessageContent> chatMessageContents)
        => this.LogUsageMetadata((GeminiMetadata)chatMessageContents[0].Metadata!);

    private List<ChatMessageContent> GetChatMessageContentsFromResponse(GeminiResponse geminiResponse)
        => geminiResponse.Candidates!.Select(candidate => new ChatMessageContent(
            role: candidate.Content?.Role ?? AuthorRole.Assistant,
            content: candidate.Content?.Parts[0].Text ?? string.Empty,
            modelId: this._modelId,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();

    private static GeminiRequest CreateGeminiRequest(
        ChatHistory chatHistory,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);
        var geminiRequest = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, geminiExecutionSettings);
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
}
