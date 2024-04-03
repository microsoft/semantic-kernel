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
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace.TextGeneration;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

internal sealed class HuggingFaceClient
{
    private readonly string _modelId;
    private readonly string? _apiKey;
    private readonly Uri? _endpoint;
    private readonly string _separator;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;

    private static readonly string s_namespace = typeof(HuggingFaceClient).Namespace!;

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

    internal HuggingFaceClient(
        string modelId,
        HttpClient httpClient,
        Uri? endpoint = null,
        string? apiKey = null,
        StreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(httpClient);

        endpoint ??= new Uri("https://api-inference.huggingface.co");
        this._separator = endpoint.AbsolutePath.EndsWith("/", StringComparison.InvariantCulture) ? string.Empty : "/";
        this._endpoint = endpoint;
        this._modelId = modelId;
        this._apiKey = apiKey;
        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
    }

    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        string modelId = executionSettings?.ModelId ?? this._modelId;
        var endpoint = this.GetTextGenerationEndpoint(modelId);
        var request = this.CreateTextRequest(prompt, executionSettings);
        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextGenerationResponse>(body);
        var textContents = GetTextContentsFromResponse(response, modelId);

        this.LogTextGenerationUsage(executionSettings);

        return textContents;
    }

    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        string modelId = executionSettings?.ModelId ?? this._modelId;
        var endpoint = this.GetChatGenerationEndpoint(modelId);
        var request = this.CreateChatRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<ChatCompletionResponse>(body);
        var chatContents = GetChatMessageContentsFromResponse(response, modelId);

        this.LogChatCompletionUsage(executionSettings, response);

        return chatContents;
    }

    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        string modelId = executionSettings?.ModelId ?? this._modelId;
        var endpoint = this.GetTextGenerationEndpoint(modelId);
        var request = this.CreateTextRequest(prompt, executionSettings);
        request.Stream = true;

        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingTextContent in this.ProcessTextResponseStreamAsync(responseStream, modelId, cancellationToken).ConfigureAwait(false))
        {
            yield return streamingTextContent;
        }
    }

    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        string modelId = executionSettings?.ModelId ?? this._modelId;
        var endpoint = this.GetChatGenerationEndpoint(modelId);
        var request = this.CreateChatRequest(chatHistory, executionSettings);
        request.Stream = true;

        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingChatContent in this.ProcessChatResponseStreamAsync(responseStream, modelId, cancellationToken).ConfigureAwait(false))
        {
            yield return streamingChatContent;
        }
    }

    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel,
        CancellationToken cancellationToken)
    {
        var endpoint = this.GetEmbeddingGenerationEndpoint(this._modelId);

        if (data.Count > 1)
        {
            throw new NotSupportedException("Currently this interface does not support multiple embeddings results per data item, use only one data item");
        }

        var request = new TextEmbeddingRequest
        {
            Inputs = data
        };

        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextEmbeddingResponse>(body);

        // Currently only one embedding per data is supported
        return response[0][0].ToList()!;
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
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

    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(Stream stream, string modelId, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        IAsyncEnumerator<TextGenerationStreamResponse>? responseEnumerator = null;

        try
        {
            var responseEnumerable = this.ParseTextResponseStreamAsync(stream, cancellationToken);
            responseEnumerator = responseEnumerable.GetAsyncEnumerator(cancellationToken);

            while (await responseEnumerator.MoveNextAsync().ConfigureAwait(false))
            {
                var textContent = responseEnumerator.Current!;

                yield return GetStreamingTextContentFromStreamResponse(textContent, modelId);
            }
        }
        finally
        {
            if (responseEnumerator != null)
            {
                await responseEnumerator.DisposeAsync().ConfigureAwait(false);
            }
        }
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> ProcessChatResponseStreamAsync(Stream stream, string modelId, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        IAsyncEnumerator<ChatCompletionStreamResponse>? responseEnumerator = null;

        try
        {
            var responseEnumerable = this.ParseChatResponseStreamAsync(stream, cancellationToken);
            responseEnumerator = responseEnumerable.GetAsyncEnumerator(cancellationToken);

            while (await responseEnumerator.MoveNextAsync().ConfigureAwait(false))
            {
                var content = responseEnumerator.Current!;

                yield return GetStreamingChatMessageContentFromStreamResponse(content, modelId);
            }
        }
        finally
        {
            if (responseEnumerator != null)
            {
                await responseEnumerator.DisposeAsync().ConfigureAwait(false);
            }
        }
    }

    private IAsyncEnumerable<TextGenerationStreamResponse> ParseTextResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
        => SseJsonParser.ParseAsync<TextGenerationStreamResponse>(responseStream, cancellationToken);

    private IAsyncEnumerable<ChatCompletionStreamResponse> ParseChatResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
        => SseJsonParser.ParseAsync<ChatCompletionStreamResponse>(responseStream, cancellationToken);

    private static StreamingTextContent GetStreamingTextContentFromStreamResponse(TextGenerationStreamResponse response, string modelId)
        => new(
            text: response.Token?.Text,
            modelId: modelId,
            innerContent: response,
            metadata: new TextGenerationStreamMetadata(response));

    private static StreamingChatMessageContent GetStreamingChatMessageContentFromStreamResponse(ChatCompletionStreamResponse response, string modelId)
    {
        var choice = response.Choices.FirstOrDefault();
        if (choice is not null)
        {
            var metadata = new Dictionary<string, object?>(6)
            {
                { "created", response.Created },
                { "object", response.Object },
                { "model", response.Model },
                { "system_fingerprint", response.SystemFingerprint },
                { "id", response.Id },
                { "finish_reason", choice.FinishReason },
                { "log_probs", choice.LogProbs },
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

    private TextGenerationRequest CreateTextRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(huggingFaceExecutionSettings.MaxTokens);
        var request = TextGenerationRequest.FromPromptAndExecutionSettings(prompt, huggingFaceExecutionSettings);
        return request;
    }

    private ChatCompletionRequest CreateChatRequest(
        ChatHistory chatHistory,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(huggingFaceExecutionSettings.MaxTokens);
        var request = ChatCompletionRequest.FromChatHistoryAndExecutionSettings(chatHistory, huggingFaceExecutionSettings);
        return request;
    }

    private static T DeserializeResponse<T>(string body)
    {
        try
        {
            T? deserializedResponse = JsonSerializer.Deserialize<T>(body);
            if (deserializedResponse is null)
            {
                throw new JsonException("Response is null");
            }

            return deserializedResponse;
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    private static List<ChatMessageContent> GetChatMessageContentsFromResponse(ChatCompletionResponse response, string modelId)
    {
        var chatMessageContents = new List<ChatMessageContent>();

        foreach (var choice in response.Choices!)
        {
            var metadata = new Dictionary<string, object?>(8)
            {
                { "created", response.Created },
                { "object", response.Object },
                { "model", response.Model },
                { "system_fingerprint", response.SystemFingerprint },
                { "id", response.Id },
                { "usage", response.Usage },
                { "finish_reason", choice.FinishReason },
                { "log_probs", choice.LogProbs },
            };

            chatMessageContents.Add(new ChatMessageContent(
                role: new AuthorRole(choice.Message!.Role!),
                content: choice.Message.Content,
                modelId: modelId,
                innerContent: response,
                encoding: Encoding.UTF8,
                metadata: metadata));
        }

        return chatMessageContents;
    }

    private static List<TextContent> GetTextContentsFromResponse(TextGenerationResponse response, string modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private static List<TextContent> GetTextContentsFromResponse(ImageToTextGenerationResponse response, string modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private void LogTextGenerationUsage(PromptExecutionSettings? executionSettings)
    {
        this._logger?.LogDebug(
            "HuggingFace text generation usage: ModelId: {ModelId}",
            executionSettings?.ModelId ?? this._modelId);
    }

    private void LogChatCompletionUsage(PromptExecutionSettings? executionSettings, ChatCompletionResponse chatCompletionResponse)
    {
        this._logger.Log(
        LogLevel.Debug,
        "HuggingFace chat completion usage - ModelId: {ModelId}, Prompt tokens: {PromptTokens}, Completion tokens: {CompletionTokens}, Total tokens: {TotalTokens}",
        chatCompletionResponse.Model,
        chatCompletionResponse.Usage!.PromptTokens,
        chatCompletionResponse.Usage!.CompletionTokens,
        chatCompletionResponse.Usage!.TotalTokens);

        s_promptTokensCounter.Add(chatCompletionResponse.Usage!.PromptTokens);
        s_completionTokensCounter.Add(chatCompletionResponse.Usage!.CompletionTokens);
        s_totalTokensCounter.Add(chatCompletionResponse.Usage!.TotalTokens);
    }

    private Uri GetTextGenerationEndpoint(string modelId)
        => new($"{this._endpoint}{this._separator}models/{modelId}");

    private Uri GetChatGenerationEndpoint(string modelId)
        => new($"{this._endpoint}{this._separator}v1/chat/completions");

    private Uri GetEmbeddingGenerationEndpoint(string modelId)
        => new($"{this._endpoint}{this._separator}pipeline/feature-extraction/{modelId}");

    private HttpRequestMessage CreatePost(object requestData, Uri endpoint, string? apiKey)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        this.SetRequestHeaders(httpRequestMessage);

        return httpRequestMessage;
    }

    public async Task<IReadOnlyList<TextContent>> GenerateTextFromImageAsync(ImageContent content, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        using var httpRequestMessage = this.CreateImageToTextRequest(content, executionSettings);
        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<ImageToTextGenerationResponse>(body);
        var textContents = GetTextContentsFromResponse(response, executionSettings?.ModelId ?? this._modelId);

        return textContents;
    }

    private HttpRequestMessage CreateImageToTextRequest(ImageContent content, PromptExecutionSettings? executionSettings)
    {
        var endpoint = this.GetImageToTextGenerationEndpoint(executionSettings?.ModelId ?? this._modelId);

        // Read the file into a byte array
        var imageContent = new ByteArrayContent(content.Data?.ToArray());
        imageContent.Headers.ContentType = new(content.MimeType);

        var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
        {
            Content = imageContent
        };

        this.SetRequestHeaders(request);

        return request;
    }

    private void SetRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(this.GetType()));
        if (!string.IsNullOrEmpty(this._apiKey))
        {
            request.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        }
    }

    private Uri GetImageToTextGenerationEndpoint(string modelId)
        => new($"{this._endpoint}{this._separator}models/{modelId}");
}
