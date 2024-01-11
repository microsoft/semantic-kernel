#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Represents a client for interacting with the Gemini API.
/// </summary>
internal class GeminiClient : ClientBase, IGeminiClient
{
    private readonly IHttpRequestFactory _httpRequestFactory;
    private readonly IEndpointProvider _endpointProvider;

    /// <summary>
    /// Represents a client for interacting with the Gemini API.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="configuration">Gemini configuration instance containing API key and other configuration options</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Stream Json Parser instance used for parsing JSON responses stream (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiClient(
        HttpClient httpClient,
        GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(streamJsonParser ?? new GeminiStreamJsonParser(), httpClient, logger)
    {
        this.ModelId = configuration.ModelId;
        this.EmbeddingModelId = configuration.EmbeddingModelId;
        this._httpRequestFactory = httpRequestFactory;
        this._endpointProvider = endpointProvider;
    }

    /// <inheritdoc/>
    public string? ModelId { get; }

    /// <inheritdoc/>
    public string? EmbeddingModelId { get; }

    #region PUBLIC METHODS

    /// <inheritdoc/>
    public virtual async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.VerifyModelId();
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = this._endpointProvider.GetTextGenerationEndpoint(this.ModelId);
        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = this._httpRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.DeserializeAndProcessTextResponse(body);
    }

    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.VerifyModelId();
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = this._endpointProvider.GetStreamTextGenerationEndpoint(this.ModelId);
        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = this._httpRequestFactory.CreatePost(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingTextContent in this.ProcessTextResponseStreamAsync(responseStream, cancellationToken))
        {
            yield return streamingTextContent;
        }
    }

    /// <inheritdoc/>
    public virtual async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.VerifyModelId();
        ValidateChatHistory(chatHistory);

        var endpoint = this._endpointProvider.GetChatCompletionEndpoint(this.ModelId);
        var geminiRequest = CreateGeminiRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this._httpRequestFactory.CreatePost(geminiRequest, endpoint);

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
        this.VerifyModelId();
        ValidateChatHistory(chatHistory);

        var endpoint = this._endpointProvider.GetStreamChatCompletionEndpoint(this.ModelId);
        var geminiRequest = CreateGeminiRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this._httpRequestFactory.CreatePost(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingChatMessageContent in this.ProcessChatResponseStreamAsync(responseStream, cancellationToken))
        {
            yield return streamingChatMessageContent;
        }
    }

    public virtual async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        CancellationToken cancellationToken = default)
    {
        this.VerifyEmbeddingModelId();
        Verify.NotNullOrEmpty(data);

        var endpoint = this._endpointProvider.GetEmbeddingsEndpoint(this.EmbeddingModelId);
        var geminiRequest = GeminiEmbeddingRequest.FromData(data, this.EmbeddingModelId);
        using var httpRequestMessage = this._httpRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessEmbeddingsResponse(body);
    }

    public virtual async Task<int> CountTokensAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.VerifyModelId();
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = this._endpointProvider.GetCountTokensEndpoint(this.ModelId);
        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = this._httpRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessCountTokensResponse(body);
    }

    #endregion

    #region PRIVATE METHODS

    [MemberNotNull(nameof(ModelId))]
    private void VerifyModelId()
    {
        if (this.ModelId is null)
        {
            throw new InvalidOperationException(
                "ModelId is not specified. To use this method, you have to specify ModelId in the constructor of this class.");
        }
    }

    [MemberNotNull(nameof(EmbeddingModelId))]
    private void VerifyEmbeddingModelId()
    {
        if (this.EmbeddingModelId is null)
        {
            throw new InvalidOperationException(
                "EmbeddingModelId is not specified. To use this method, you have to specify EmbeddingModelId in the constructor of this class.");
        }
    }

    private static int DeserializeAndProcessCountTokensResponse(string body)
    {
        var node = DeserializeResponse<JsonNode>(body);
        return node["totalTokens"]?.GetValue<int>() ?? throw new KernelException("Invalid response from model");
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

    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var geminiResponse in this.ProcessResponseStreamAsync(responseStream, cancellationToken))
        {
            foreach (var textContent in this.ProcessTextResponse(geminiResponse))
            {
                yield return GetStreamingTextContentFromTextContent(textContent);
            }
        }
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> ProcessChatResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var geminiResponse in this.ProcessResponseStreamAsync(responseStream, cancellationToken))
        {
            foreach (var chatMessageContent in this.ProcessChatResponse(geminiResponse))
            {
                yield return GetStreamingChatContentFromChatContent(chatMessageContent);
            }
        }
    }

    private List<TextContent> DeserializeAndProcessTextResponse(string body)
    {
        var geminiResponse = DeserializeResponse<GeminiResponse>(body);
        return this.ProcessTextResponse(geminiResponse);
    }

    private List<ChatMessageContent> DeserializeAndProcessChatResponse(string body)
    {
        var geminiResponse = DeserializeResponse<GeminiResponse>(body);
        return this.ProcessChatResponse(geminiResponse);
    }

    private static List<ReadOnlyMemory<float>> DeserializeAndProcessEmbeddingsResponse(string body)
    {
        var embeddingsResponse = DeserializeResponse<GeminiEmbeddingResponse>(body);
        return ProcessEmbeddingsResponse(embeddingsResponse);
    }

    private List<TextContent> ProcessTextResponse(GeminiResponse geminiResponse)
    {
        var textContents = geminiResponse.Candidates.Select(candidate => new TextContent(
            text: candidate.Content.Parts[0].Text,
            modelId: this.ModelId,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();
        this.LogUsageMetadata((GeminiMetadata)textContents[0].Metadata!);
        return textContents;
    }

    private List<ChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
    {
        var chatMessageContents = geminiResponse.Candidates.Select(candidate => new ChatMessageContent(
            role: candidate.Content.Role ?? AuthorRole.Assistant,
            content: candidate.Content.Parts[0].Text,
            modelId: this.ModelId,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();
        this.LogUsageMetadata((GeminiMetadata)chatMessageContents[0].Metadata!);
        return chatMessageContents;
    }

    private static List<ReadOnlyMemory<float>> ProcessEmbeddingsResponse(GeminiEmbeddingResponse embeddingsResponse)
        => embeddingsResponse.Embeddings.Select(embedding => embedding.Values).ToList();

    private static GeminiRequest CreateGeminiRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);
        var geminiRequest = GeminiRequest.FromPromptAndExecutionSettings(prompt, geminiExecutionSettings);
        return geminiRequest;
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

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
        => new(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata,
            choiceIndex: ((GeminiMetadata)textContent.Metadata!).Index);

    private static StreamingChatMessageContent GetStreamingChatContentFromChatContent(ChatMessageContent chatMessageContent)
        => new(
            role: chatMessageContent.Role,
            content: chatMessageContent.Content,
            modelId: chatMessageContent.ModelId,
            innerContent: chatMessageContent.InnerContent,
            metadata: chatMessageContent.Metadata,
            choiceIndex: ((GeminiMetadata)chatMessageContent.Metadata!).Index);

    #endregion
}
