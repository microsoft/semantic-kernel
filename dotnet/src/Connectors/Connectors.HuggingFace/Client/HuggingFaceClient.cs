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
using Microsoft.SemanticKernel.Connectors.HuggingFace.TextGeneration;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

internal sealed class HuggingFaceClient
{
    private readonly IStreamJsonParser _streamJsonParser;
    private readonly string _modelId;
    private readonly string? _apiKey;
    private readonly Uri? _endpoint;
    private readonly string _separator;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;

    internal HuggingFaceClient(
        string modelId,
        HttpClient httpClient,
        Uri? endpoint = null,
        string? apiKey = null,
        IStreamJsonParser? streamJsonParser = null,
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
        this._streamJsonParser = streamJsonParser ?? new TextGenerationStreamJsonParser();
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
        var textContents = GetTextContentFromResponse(response, modelId);

        this.LogTextGenerationUsage(executionSettings);

        return textContents;
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

        foreach (var streamingTextContent in this.ProcessTextResponseStream(responseStream, modelId))
        {
            yield return streamingTextContent;
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

    private IEnumerable<StreamingTextContent> ProcessTextResponseStream(Stream stream, string modelId)
        => from response in this.ParseTextResponseStream(stream)
           from textContent in this.GetTextStreamContentsFromResponse(response, modelId)
           select GetStreamingTextContentFromTextContent(textContent);

    private IEnumerable<TextGenerationStreamResponse> ParseTextResponseStream(Stream responseStream)
        => this._streamJsonParser.Parse(responseStream).Select(DeserializeResponse<TextGenerationStreamResponse>);

    private List<TextContent> GetTextStreamContentsFromResponse(TextGenerationStreamResponse response, string modelId)
    {
        return new List<TextContent>
        {
            new(text: response.Token?.Text,
                modelId: modelId,
                innerContent: response,
                metadata: new TextGenerationStreamMetadata(response))
        };
    }

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
        => new(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata);

    private TextGenerationRequest CreateTextRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(huggingFaceExecutionSettings.MaxTokens);
        var request = TextGenerationRequest.FromPromptAndExecutionSettings(prompt, huggingFaceExecutionSettings);
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

    private static List<TextContent> GetTextContentFromResponse(TextGenerationResponse response, string modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private static List<TextContent> GetTextContentFromResponse(ImageToTextGenerationResponse response, string modelId)
        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private void LogTextGenerationUsage(PromptExecutionSettings? executionSettings)
    {
        this._logger?.LogDebug(
            "HuggingFace text generation usage: ModelId: {ModelId}",
            executionSettings?.ModelId ?? this._modelId);
    }

    private Uri GetTextGenerationEndpoint(string modelId)
        => new($"{this._endpoint}{this._separator}models/{modelId}");

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
        var textContents = GetTextContentFromResponse(response, executionSettings?.ModelId ?? this._modelId);

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
