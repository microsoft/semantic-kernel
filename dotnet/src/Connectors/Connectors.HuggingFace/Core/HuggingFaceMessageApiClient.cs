// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// This class is responsible for making HTTP requests to the HuggingFace Inference API - Chat Completion Message API
/// <see href="https://huggingface.co/docs/text-generation-inference/main/en/messages_api" />
/// </summary>
internal sealed class HuggingFaceMessageApiClient
{
    private readonly HuggingFaceClient _clientCore;

    private static readonly string s_namespace = typeof(HuggingFaceChatCompletionService).Namespace!;

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
            description: "Number of total tokens used");

    internal HuggingFaceMessageApiClient(
        HttpClient httpClient,
        string? modelId = null,
        Uri? endpoint = null,
        string? apiKey = null,
        ILogger? logger = null)
    {
        this._clientCore = new(
            httpClient,
            modelId,
            endpoint,
            apiKey,
            logger);
    }

    internal async IAsyncEnumerable<StreamingChatMessageContent> StreamCompleteChatMessageAsync(
      ChatHistory chatHistory,
      PromptExecutionSettings? executionSettings,
      [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        string? modelId = executionSettings?.ModelId ?? this._clientCore.ModelId;
        var endpoint = this.GetChatGenerationEndpoint();

        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);

        var request = this.CreateChatRequest(chatHistory, huggingFaceExecutionSettings, modelId);
        request.Stream = true;

        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId ?? string.Empty, this._clientCore.ModelProvider, chatHistory, huggingFaceExecutionSettings);
        HttpResponseMessage? httpResponseMessage = null;
        Stream? responseStream = null;
        try
        {
            using var httpRequestMessage = this._clientCore.CreatePost(request, endpoint, this._clientCore.ApiKey);
            httpResponseMessage = await this._clientCore.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            responseStream = await httpResponseMessage.Content.ReadAsStreamAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            activity?.SetError(ex);
            httpResponseMessage?.Dispose();
            responseStream?.Dispose();
            throw;
        }

        var responseEnumerator = this.ProcessChatResponseStreamAsync(responseStream, modelId, cancellationToken)
            .GetAsyncEnumerator(cancellationToken);
        List<StreamingChatMessageContent>? streamedContents = activity is not null ? [] : null;
        try
        {
            while (true)
            {
                try
                {
                    if (!await responseEnumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        break;
                    }
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    throw;
                }

                streamedContents?.Add(responseEnumerator.Current);
                yield return responseEnumerator.Current;
            }
        }
        finally
        {
            activity?.EndStreaming(streamedContents);
            httpResponseMessage?.Dispose();
            responseStream?.Dispose();
            await responseEnumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    internal async Task<IReadOnlyList<ChatMessageContent>> CompleteChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        string? modelId = executionSettings?.ModelId ?? this._clientCore.ModelId;
        var endpoint = this.GetChatGenerationEndpoint();

        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = this.CreateChatRequest(chatHistory, huggingFaceExecutionSettings, modelId);

        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId ?? string.Empty, this._clientCore.ModelProvider, chatHistory, huggingFaceExecutionSettings);
        using var httpRequestMessage = this._clientCore.CreatePost(request, endpoint, this._clientCore.ApiKey);

        ChatCompletionResponse response;
        try
        {
            string body = await this._clientCore.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
                .ConfigureAwait(false);

            response = HuggingFaceClient.DeserializeResponse<ChatCompletionResponse>(body);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        var chatContents = GetChatMessageContentsFromResponse(response, modelId);

        activity?.SetCompletionResponse(chatContents, response.Usage?.PromptTokens, response.Usage?.CompletionTokens);
        this.LogChatCompletionUsage(huggingFaceExecutionSettings, response);

        return chatContents;
    }

    private void LogChatCompletionUsage(HuggingFacePromptExecutionSettings executionSettings, ChatCompletionResponse chatCompletionResponse)
    {
        if (chatCompletionResponse.Usage is null)
        {
            this._clientCore.Logger.LogDebug("Token usage information unavailable.");
            return;
        }

        if (this._clientCore.Logger.IsEnabled(LogLevel.Information))
        {
            this._clientCore.Logger.LogInformation(
                "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}. Total tokens: {TotalTokens}. ModelId: {ModelId}.",
                chatCompletionResponse.Usage.PromptTokens,
                chatCompletionResponse.Usage.CompletionTokens,
                chatCompletionResponse.Usage.TotalTokens,
                chatCompletionResponse.Model);
        }

        s_promptTokensCounter.Add(chatCompletionResponse.Usage.PromptTokens);
        s_completionTokensCounter.Add(chatCompletionResponse.Usage.CompletionTokens);
        s_totalTokensCounter.Add(chatCompletionResponse.Usage.TotalTokens);
    }

    private static List<ChatMessageContent> GetChatMessageContentsFromResponse(ChatCompletionResponse response, string? modelId)
    {
        var chatMessageContents = new List<ChatMessageContent>();

        foreach (var choice in response.Choices!)
        {
            var metadata = new HuggingFaceChatCompletionMetadata
            {
                Id = response.Id,
                Model = response.Model,
                @Object = response.Object,
                SystemFingerPrint = response.SystemFingerprint,
                Created = response.Created,
                FinishReason = choice.FinishReason,
                LogProbs = choice.LogProbs,
                UsageCompletionTokens = response.Usage?.CompletionTokens,
                UsagePromptTokens = response.Usage?.PromptTokens,
                UsageTotalTokens = response.Usage?.TotalTokens,
            };

            chatMessageContents.Add(new ChatMessageContent(
                role: new AuthorRole(choice.Message?.Role ?? AuthorRole.Assistant.ToString()),
                content: choice.Message?.Content,
                modelId: response.Model,
                innerContent: response,
                encoding: Encoding.UTF8,
                metadata: metadata));
        }

        return chatMessageContents;
    }

    private static StreamingChatMessageContent GetStreamingChatMessageContentFromStreamResponse(ChatCompletionStreamResponse response, string? modelId)
    {
        var choice = response.Choices?.FirstOrDefault();
        if (choice is not null)
        {
            var metadata = new HuggingFaceChatCompletionMetadata
            {
                Id = response.Id,
                Model = response.Model,
                @Object = response.Object,
                SystemFingerPrint = response.SystemFingerprint,
                Created = response.Created,
                FinishReason = choice.FinishReason,
                LogProbs = choice.LogProbs,
            };

            var streamChat = new StreamingChatMessageContent(
                choice.Delta?.Role is not null ? new AuthorRole(choice.Delta.Role) : null,
                choice.Delta?.Content,
                response,
                choice.Index,
                modelId,
                Encoding.UTF8,
                metadata);

            return streamChat;
        }

        throw new KernelException("Unexpected response from model")
        {
            Data = { { "ResponseData", response } },
        };
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> ProcessChatResponseStreamAsync(Stream stream, string? modelId, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var content in this.ParseChatResponseStreamAsync(stream, cancellationToken).ConfigureAwait(false))
        {
            yield return GetStreamingChatMessageContentFromStreamResponse(content, modelId);
        }
    }

    private ChatCompletionRequest CreateChatRequest(
        ChatHistory chatHistory,
        HuggingFacePromptExecutionSettings huggingFaceExecutionSettings,
        string? modelId)
    {
        HuggingFaceClient.ValidateMaxTokens(huggingFaceExecutionSettings.MaxTokens);

        if (this._clientCore.Logger.IsEnabled(LogLevel.Trace))
        {
            this._clientCore.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory, JsonOptionsCache.ChatHistory),
                JsonSerializer.Serialize(huggingFaceExecutionSettings));
        }

        var request = ChatCompletionRequest.FromChatHistoryAndExecutionSettings(chatHistory, huggingFaceExecutionSettings, modelId);
        return request;
    }

    private IAsyncEnumerable<ChatCompletionStreamResponse> ParseChatResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
        => SseJsonParser.ParseAsync<ChatCompletionStreamResponse>(responseStream, cancellationToken);

    private Uri GetChatGenerationEndpoint()
        => new($"{this._clientCore.Endpoint}{this._clientCore.Separator}v1/chat/completions");
}
