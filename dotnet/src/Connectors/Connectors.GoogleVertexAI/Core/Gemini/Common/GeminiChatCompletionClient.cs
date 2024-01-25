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
        ValidateChatHistory(chatHistory);

        var endpoint = this.EndpointProvider.GetChatCompletionEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.DeserializeAndProcessChatResponse(body);
    }

    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ValidateChatHistory(chatHistory);

        var endpoint = this.EndpointProvider.GetStreamChatCompletionEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        foreach (var streamingChatMessageContent in this.ProcessChatResponseStream(responseStream))
        {
            yield return streamingChatMessageContent;
        }
    }

    private static void ValidateChatHistory(ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);

        if (chatHistory.Any(message => message.Role == AuthorRole.System))
        {
            // TODO: Temporary solution, maybe we can support system messages with two messages in the chat history (one from the user and one from the assistant)
            throw new NotSupportedException("Gemini API currently doesn't support system messages.");
        }

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

    private IEnumerable<StreamingChatMessageContent> ProcessChatResponseStream(
        Stream responseStream)
    {
        foreach (var geminiResponse in this.ProcessResponseStream(responseStream))
        {
            foreach (var chatMessageContent in this.ProcessChatResponse(geminiResponse))
            {
                yield return GetStreamingChatContentFromChatContent(chatMessageContent);
            }
        }
    }

    private IEnumerable<GeminiResponse> ProcessResponseStream(
        Stream responseStream)
    {
        foreach (string json in this._streamJsonParser.Parse(responseStream))
        {
            yield return DeserializeResponse<GeminiResponse>(json);
        }
    }

    private List<ChatMessageContent> DeserializeAndProcessChatResponse(string body)
    {
        var geminiResponse = DeserializeResponse<GeminiResponse>(body);
        return this.ProcessChatResponse(geminiResponse);
    }

    private List<ChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
    {
        if (geminiResponse.Candidates == null || !geminiResponse.Candidates.Any())
        {
            throw new KernelException("Gemini API doesn't return any data.");
        }

        var chatMessageContents = geminiResponse.Candidates.Select(candidate => new ChatMessageContent(
            role: candidate.Content?.Role ?? AuthorRole.Assistant,
            content: candidate.Content?.Parts[0].Text ?? string.Empty,
            modelId: this._modelId,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();
        this.LogUsageMetadata((GeminiMetadata)chatMessageContents[0].Metadata!);
        return chatMessageContents;
    }

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
