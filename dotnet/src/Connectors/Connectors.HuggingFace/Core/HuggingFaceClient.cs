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
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class HuggingFaceClient
{
    private readonly HttpClient _httpClient;

    internal string ModelProvider => "huggingface";
    internal string? ModelId { get; }
    internal string? ApiKey { get; }
    internal Uri Endpoint { get; }
    internal string Separator { get; }
    internal ILogger Logger { get; }

    internal HuggingFaceClient(
        HttpClient httpClient,
        string? modelId = null,
        Uri? endpoint = null,
        string? apiKey = null,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);

        endpoint ??= httpClient.BaseAddress;
        if (string.IsNullOrWhiteSpace(modelId) && endpoint is null)
        {
            throw new InvalidOperationException("A valid model id or endpoint must be provided.");
        }

        endpoint ??= new Uri("https://api-inference.huggingface.co");
        this.Separator = endpoint.AbsolutePath.EndsWith("/", StringComparison.InvariantCulture) ? string.Empty : "/";
        this.Endpoint = endpoint;
        this.ModelId = modelId;
        this.ApiKey = apiKey;
        this._httpClient = httpClient;
        this.Logger = logger ?? NullLogger.Instance;
    }

    #region ClientCore
    internal static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    internal static void ValidateMaxNewTokens(int? maxNewTokens)
    {
        if (maxNewTokens is < 0)
        {
            throw new ArgumentException($"MaxNewTokens {maxNewTokens} is not valid, the value must be greater than or equal to zero");
        }
    }

    internal async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken)
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
            return JsonSerializer.Deserialize<T>(body) ??
                throw new JsonException("Response is null");
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
        string? modelId = executionSettings?.ModelId ?? this.ModelId;
        var endpoint = this.GetTextGenerationEndpoint(modelId);

        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = this.CreateTextRequest(prompt, huggingFaceExecutionSettings);

        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId ?? string.Empty, this.ModelProvider, prompt, huggingFaceExecutionSettings);
        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        TextGenerationResponse response;
        try
        {
            string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
                .ConfigureAwait(false);

            response = DeserializeResponse<TextGenerationResponse>(body);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        var textContents = GetTextContentsFromResponse(response, modelId);

        activity?.SetCompletionResponse(textContents);
        this.LogTextGenerationUsage(huggingFaceExecutionSettings);

        return textContents;
    }

    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        string? modelId = executionSettings?.ModelId ?? this.ModelId;
        var endpoint = this.GetTextGenerationEndpoint(modelId);

        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = this.CreateTextRequest(prompt, huggingFaceExecutionSettings);
        request.Stream = true;

        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId ?? string.Empty, this.ModelProvider, prompt, huggingFaceExecutionSettings);
        HttpResponseMessage? httpResponseMessage = null;
        Stream? responseStream = null;
        try
        {
            using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);
            httpResponseMessage = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            responseStream = await httpResponseMessage.Content.ReadAsStreamAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            activity?.SetError(ex);
            httpResponseMessage?.Dispose();
            responseStream?.Dispose();
            throw;
        }

        var responseEnumerator = this.ProcessTextResponseStreamAsync(responseStream, modelId, cancellationToken)
            .GetAsyncEnumerator(cancellationToken);
        List<StreamingTextContent>? streamedContents = activity is not null ? [] : null;
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

    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(Stream stream, string? modelId, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var content in this.ParseTextResponseStreamAsync(stream, cancellationToken).ConfigureAwait(false))
        {
            yield return GetStreamingTextContentFromStreamResponse(content, modelId);
        }
    }

    private IAsyncEnumerable<TextGenerationStreamResponse> ParseTextResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
        => SseJsonParser.ParseAsync<TextGenerationStreamResponse>(responseStream, cancellationToken);

    private static StreamingTextContent GetStreamingTextContentFromStreamResponse(TextGenerationStreamResponse response, string? modelId)
        => new(
            text: response.Token?.Text,
            modelId: modelId,
            innerContent: response,
            metadata: new HuggingFaceTextGenerationStreamMetadata(response));

    private TextGenerationRequest CreateTextRequest(
        string prompt,
        HuggingFacePromptExecutionSettings huggingFaceExecutionSettings)
    {
        ValidateMaxNewTokens(huggingFaceExecutionSettings.MaxNewTokens);
        var request = TextGenerationRequest.FromPromptAndExecutionSettings(prompt, huggingFaceExecutionSettings);
        return request;
    }

    private static List<TextContent> GetTextContentsFromResponse(TextGenerationResponse response, string? modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8, new HuggingFaceTextGenerationMetadata(response))).ToList();

    private static List<TextContent> GetTextContentsFromResponse(ImageToTextGenerationResponse response, string? modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private void LogTextGenerationUsage(HuggingFacePromptExecutionSettings executionSettings)
    {
        if (this.Logger.IsEnabled(LogLevel.Debug))
        {
            this.Logger.LogDebug(
                "HuggingFace text generation usage: ModelId: {ModelId}",
                executionSettings.ModelId ?? this.ModelId);
        }
    }
    private Uri GetTextGenerationEndpoint(string? modelId)
        => string.IsNullOrWhiteSpace(modelId) ? this.Endpoint : new($"{this.Endpoint}{this.Separator}models/{modelId}");

    #endregion

    #region Embeddings

    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel,
        CancellationToken cancellationToken)
    {
        var endpoint = this.GetEmbeddingGenerationEndpoint(this.ModelId);

        var request = new TextEmbeddingRequest
        {
            Inputs = data
        };

        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextEmbeddingResponse>(body);

        return response;
    }

    private Uri GetEmbeddingGenerationEndpoint(string? modelId)
        => string.IsNullOrWhiteSpace(modelId) ? this.Endpoint : new($"{this.Endpoint}{this.Separator}pipeline/feature-extraction/{modelId}");

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
        var imageContent = new ByteArrayContent(content.Data?.ToArray() ?? []);
        imageContent.Headers.ContentType = new(content.MimeType ?? string.Empty);

        var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
        {
            Content = imageContent
        };

        this.SetRequestHeaders(request);

        return request;
    }

    private Uri GetImageToTextGenerationEndpoint(string? modelId)
        => string.IsNullOrWhiteSpace(modelId) ? this.Endpoint : new($"{this.Endpoint}{this.Separator}models/{modelId}");

    #endregion
}
