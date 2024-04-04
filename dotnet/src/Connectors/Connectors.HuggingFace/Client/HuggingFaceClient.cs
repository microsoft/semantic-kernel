// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
using Microsoft.SemanticKernel.Connectors.HuggingFace.Client.Models;
using Microsoft.SemanticKernel.Connectors.HuggingFace.TextGeneration;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

internal sealed class HuggingFaceClient
{
    private readonly HttpClient _httpClient;
    private readonly HuggingFaceOpenAIClient _openAIClient;

    internal string ModelId { get; }
    internal string? ApiKey { get; }
    internal Uri? Endpoint { get; }
    internal string Separator { get; }
    internal ILogger Logger { get; }

    internal HuggingFaceClient(
        string modelId,
        HttpClient httpClient,
        Uri? endpoint = null,
        string? apiKey = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(httpClient);

        endpoint ??= new Uri("https://api-inference.huggingface.co");
        this.Separator = endpoint.AbsolutePath.EndsWith("/", StringComparison.InvariantCulture) ? string.Empty : "/";
        this.Endpoint = endpoint;
        this.ModelId = modelId;
        this.ApiKey = apiKey;
        this._httpClient = httpClient;
        this.Logger = logger ?? NullLogger.Instance;

        this._openAIClient = new HuggingFaceOpenAIClient(this);
    }

    #region ClientCore
    internal static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    internal async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);

        return body;
    }

    internal async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    internal static T DeserializeResponse<T>(string body)
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

    internal void SetRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(this.GetType()));
        if (!string.IsNullOrEmpty(this.ApiKey))
        {
            request.Headers.Add("Authorization", $"Bearer {this.ApiKey}");
        }
    }

    internal HttpRequestMessage CreatePost(object requestData, Uri endpoint, string? apiKey)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        this.SetRequestHeaders(httpRequestMessage);

        return httpRequestMessage;
    }

    #endregion

    #region Text Generation

    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        string modelId = executionSettings?.ModelId ?? this.ModelId;
        var endpoint = this.GetTextGenerationEndpoint(modelId);
        var request = this.CreateTextRequest(prompt, executionSettings);
        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextGenerationResponse>(body);
        var textContents = GetTextContentsFromResponse(response, modelId);

        this.LogTextGenerationUsage(executionSettings);

        return textContents;
    }

    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        string modelId = executionSettings?.ModelId ?? this.ModelId;
        var endpoint = this.GetTextGenerationEndpoint(modelId);
        var request = this.CreateTextRequest(prompt, executionSettings);
        request.Stream = true;

        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingTextContent in this.ProcessTextResponseStreamAsync(responseStream, modelId, cancellationToken).ConfigureAwait(false))
        {
            yield return streamingTextContent;
        }
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

    private IAsyncEnumerable<TextGenerationStreamResponse> ParseTextResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
        => SseJsonParser.ParseAsync<TextGenerationStreamResponse>(responseStream, cancellationToken);

    private static StreamingTextContent GetStreamingTextContentFromStreamResponse(TextGenerationStreamResponse response, string modelId)
        => new(
            text: response.Token?.Text,
            modelId: modelId,
            innerContent: response,
            metadata: new TextGenerationStreamMetadata(response));

    private TextGenerationRequest CreateTextRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(huggingFaceExecutionSettings.MaxTokens);
        var request = TextGenerationRequest.FromPromptAndExecutionSettings(prompt, huggingFaceExecutionSettings);
        return request;
    }

    private static List<TextContent> GetTextContentsFromResponse(TextGenerationResponse response, string modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private static List<TextContent> GetTextContentsFromResponse(ImageToTextGenerationResponse response, string modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private void LogTextGenerationUsage(PromptExecutionSettings? executionSettings)
    {
        this.Logger?.LogDebug(
            "HuggingFace text generation usage: ModelId: {ModelId}",
            executionSettings?.ModelId ?? this.ModelId);
    }
    private Uri GetTextGenerationEndpoint(string modelId)
        => new($"{this.Endpoint}{this.Separator}models/{modelId}");

    #endregion

    #region Embeddings

    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel,
        CancellationToken cancellationToken)
    {
        var endpoint = this.GetEmbeddingGenerationEndpoint(this.ModelId);

        if (data.Count > 1)
        {
            throw new NotSupportedException("Currently this interface does not support multiple embeddings results per data item, use only one data item");
        }

        var request = new TextEmbeddingRequest
        {
            Inputs = data
        };

        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextEmbeddingResponse>(body);

        // Currently only one embedding per data is supported
        return response[0][0].ToList()!;
    }

    private Uri GetEmbeddingGenerationEndpoint(string modelId)
        => new($"{this.Endpoint}{this.Separator}pipeline/feature-extraction/{modelId}");

    #endregion

    #region Image to Text

    public async Task<IReadOnlyList<TextContent>> GenerateTextFromImageAsync(ImageContent content, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        using var httpRequestMessage = this.CreateImageToTextRequest(content, executionSettings);
        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<ImageToTextGenerationResponse>(body);
        var textContents = GetTextContentsFromResponse(response, executionSettings?.ModelId ?? this.ModelId);

        return textContents;
    }

    private HttpRequestMessage CreateImageToTextRequest(ImageContent content, PromptExecutionSettings? executionSettings)
    {
        var endpoint = this.GetImageToTextGenerationEndpoint(executionSettings?.ModelId ?? this.ModelId);

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

    private Uri GetImageToTextGenerationEndpoint(string modelId)
        => new($"{this.Endpoint}{this.Separator}models/{modelId}");

    #endregion

    #region Chat Commpletion

    internal Task<IReadOnlyList<ChatMessageContent>> GenerateChatAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings, CancellationToken cancellationToken)
        => this._openAIClient.GenerateChatAsync(chatHistory, executionSettings, cancellationToken);

    internal IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings, CancellationToken cancellationToken)
        => this._openAIClient.StreamGenerateChatAsync(chatHistory, executionSettings, cancellationToken);

    #endregion
}
