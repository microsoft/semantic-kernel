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

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class HuggingFaceClient : IHuggingFaceClient
{
    private readonly IStreamJsonParser _streamJsonParser;
    private readonly string _modelId;
    private readonly string? _apiKey;

    private IHttpRequestFactory HttpRequestFactory { get; }
    private IEndpointProvider EndpointProvider { get; }
    private HttpClient HttpClient { get; }
    private ILogger Logger { get; }

    internal HuggingFaceClient(
        string modelId,
        HttpClient httpClient,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        string? apiKey = null,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this._modelId = modelId;
        this._apiKey = apiKey;
        this.HttpClient = httpClient;
        this.HttpRequestFactory = httpRequestFactory;
        this.EndpointProvider = endpointProvider;
        this.Logger = logger ?? NullLogger.Instance;
        this._streamJsonParser = streamJsonParser ?? new TextGenerationStreamJsonParser();
    }

    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(string prompt, PromptExecutionSettings? executionSettings, CancellationToken cancellationToken)
    {
        var endpoint = this.EndpointProvider.GetTextGenerationEndpoint(executionSettings?.ModelId ?? this._modelId);
        var request = this.CreateTextRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint, this._apiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextGenerationResponse>(body);
        var textContents = GetTextContentFromResponse(response, executionSettings?.ModelId ?? this._modelId);

        this.LogTextGenerationUsage(executionSettings);

        return textContents;
    }

    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.GetTextGenerationEndpoint(executionSettings?.ModelId ?? this._modelId);
        var request = this.CreateTextRequest(prompt, executionSettings);
        request.Stream = true;

        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint, this._apiKey);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        foreach (var streamingTextContent in this.ProcessTextResponseStream(responseStream, executionSettings?.ModelId ?? this._modelId))
        {
            yield return streamingTextContent;
        }
    }

    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.GetEmbeddingGenerationEndpoint(this._modelId);

        var request = new TextEmbeddingRequest()
        {
            Input = data
        };

        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint, this._apiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<TextEmbeddingResponse>(body);

        return response?.Embeddings?.Select(l => l.Embedding).ToList()!;
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
        using var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);

        return body;
    }

    private async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
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
            new(text: response.GeneratedText,
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

    private void LogTextGenerationUsage(PromptExecutionSettings? executionSettings)
    {
        this.Logger?.LogDebug(
            "HuggingFace text generation usage: ModelId: {ModelId}",
            executionSettings?.ModelId ?? this._modelId);
    }
}
