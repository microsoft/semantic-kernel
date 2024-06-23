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

    internal string ModelId { get; }

    internal string? ApiKey { get; }

    internal Uri Endpoint { get; }

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

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #region ClientCore
After:
    #region ClientCore
*/


    #region ClientCore

    internal static void ValidateMaxTokens(int? maxTokens)

    {
        if (maxTokens is < 1)

        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    internal static void ValidateMaxNewTokens(int? maxNewTokens)
After:
    internal static void ValidateMaxNewTokens(int? maxNewTokens)
*/


    internal static void ValidateMaxNewTokens(int? maxNewTokens)

    {
        if (maxNewTokens is < 0)

        {
            throw new ArgumentException($"MaxNewTokens {maxNewTokens} is not valid, the value must be greater than or equal to zero");

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    internal async Task<string> SendRequestAndGetStringBodyAsync(
After:
    internal async Task<string> SendRequestAndGetStringBodyAsync(
*/


    internal async Task<string> SendRequestAndGetStringBodyAsync(

        HttpRequestMessage httpRequestMessage,

        CancellationToken cancellationToken)

    {
        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)

            .ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()

            .ConfigureAwait(false);

        return body;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    internal async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
After:
    internal async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
*/


    internal async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(

        HttpRequestMessage httpRequestMessage,

        CancellationToken cancellationToken)

    {
        var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)

            .ConfigureAwait(false);

        return response;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    internal static T DeserializeResponse<T>(string body)
After:
    internal static T DeserializeResponse<T>(string body)
*/


    internal static T DeserializeResponse<T>(string body)

    {
        try

        {
            return JsonSerializer.Deserialize<T>(body) ??

                throw new JsonException("Response is null");

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

        catch (JsonException exc)
After:
        }
        catch (JsonException exc)
*/
        }
        catch (JsonException exc)

        {
            throw new KernelException("Unexpected response from model", exc)

            {
                Data = { { "ResponseData", body } },
            };

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    internal void SetRequestHeaders(HttpRequestMessage request)
After:
    internal void SetRequestHeaders(HttpRequestMessage request)
*/


    internal void SetRequestHeaders(HttpRequestMessage request)

    {
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);

        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(this.GetType()));

        if (!string.IsNullOrEmpty(this.ApiKey))

        {
            request.Headers.Add("Authorization", $"Bearer {this.ApiKey}");

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    internal HttpRequestMessage CreatePost(object requestData, Uri endpoint, string? apiKey)
After:
    internal HttpRequestMessage CreatePost(object requestData, Uri endpoint, string? apiKey)
*/


    internal HttpRequestMessage CreatePost(object requestData, Uri endpoint, string? apiKey)

    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);

        this.SetRequestHeaders(httpRequestMessage);

        return httpRequestMessage;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #endregion
After:
    #endregion
*/

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #region Text Generation
After:
    #region Text Generation
*/
    }

    #endregion

    #region Text Generation
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
After:
    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
*/


    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(

        string prompt,

        PromptExecutionSettings? executionSettings,

        CancellationToken cancellationToken)

    {
        string modelId = executionSettings?.ModelId ?? this.ModelId;

        var endpoint = this.GetTextGenerationEndpoint(modelId);

        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);

        var request = this.CreateTextRequest(prompt, huggingFaceExecutionSettings);

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId, this.ModelProvider, prompt, huggingFaceExecutionSettings);
After:
        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId, this.ModelProvider, prompt, huggingFaceExecutionSettings);
*/

        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId, this.ModelProvider, prompt, huggingFaceExecutionSettings);


/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        TextGenerationResponse response;
After:
        TextGenerationResponse response;
*/
        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        TextGenerationResponse response;

        try

        {
            string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)

                .ConfigureAwait(false);

            response = DeserializeResponse<TextGenerationResponse>(body);

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

        catch (Exception ex) when (activity is not null)
After:
        }
        catch (Exception ex) when (activity is not null)
*/
        }
        catch (Exception ex) when (activity is not null)

        {
            activity.SetError(ex);

            throw;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }
After:
        }
*/
        }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        var textContents = GetTextContentsFromResponse(response, modelId);
After:
        var textContents = GetTextContentsFromResponse(response, modelId);
*/


        var textContents = GetTextContentsFromResponse(response, modelId);

        activity?.SetCompletionResponse(textContents);

        this.LogTextGenerationUsage(huggingFaceExecutionSettings);

        return textContents;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
After:
    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
*/


    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(

        string prompt,

        PromptExecutionSettings? executionSettings,

        [EnumeratorCancellation] CancellationToken cancellationToken)

    {
        string modelId = executionSettings?.ModelId ?? this.ModelId;

        var endpoint = this.GetTextGenerationEndpoint(modelId);

        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);

        var request = this.CreateTextRequest(prompt, huggingFaceExecutionSettings);

        request.Stream = true;

        using var activity = ModelDiagnostics.StartCompletionActivity(endpoint, modelId, this.ModelProvider, prompt, huggingFaceExecutionSettings);

        HttpResponseMessage? httpResponseMessage = null;

        Stream? responseStream = null;

        try

        {
            using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

            httpResponseMessage = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

            responseStream = await httpResponseMessage.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

        catch (Exception ex)
After:
        }
        catch (Exception ex)
*/
        }
        catch (Exception ex)

        {
            activity?.SetError(ex);

            httpResponseMessage?.Dispose();

            responseStream?.Dispose();

            throw;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }
After:
        }
*/
        }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        var responseEnumerator = this.ProcessTextResponseStreamAsync(responseStream, modelId, cancellationToken)
After:
        var responseEnumerator = this.ProcessTextResponseStreamAsync(responseStream, modelId, cancellationToken)
*/


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

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
                    }

                }

                catch (Exception ex) when (activity is not null)
After:
                    }
                }
                catch (Exception ex) when (activity is not null)
*/
                    }
                }
                catch (Exception ex) when (activity is not null)

                {
                    activity.SetError(ex);

                    throw;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
                }
After:
                }
*/
                }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
                streamedContents?.Add(responseEnumerator.Current);
After:
                streamedContents?.Add(responseEnumerator.Current);
*/


                streamedContents?.Add(responseEnumerator.Current);

                yield return responseEnumerator.Current;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
            }

        }
After:
            }
        }
*/
            }
        }

        finally

        {
            activity?.EndStreaming(streamedContents);

            httpResponseMessage?.Dispose();

            responseStream?.Dispose();

            await responseEnumerator.DisposeAsync().ConfigureAwait(false);

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(Stream stream, string modelId, [EnumeratorCancellation] CancellationToken cancellationToken)
After:
    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(Stream stream, string modelId, [EnumeratorCancellation] CancellationToken cancellationToken)
*/


    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(Stream stream, string modelId, [EnumeratorCancellation] CancellationToken cancellationToken)

    {
        await foreach (var content in this.ParseTextResponseStreamAsync(stream, cancellationToken).ConfigureAwait(false))

        {
            yield return GetStreamingTextContentFromStreamResponse(content, modelId);

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    private IAsyncEnumerable<TextGenerationStreamResponse> ParseTextResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
After:
    private IAsyncEnumerable<TextGenerationStreamResponse> ParseTextResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)
*/


    private IAsyncEnumerable<TextGenerationStreamResponse> ParseTextResponseStreamAsync(Stream responseStream, CancellationToken cancellationToken)

        => SseJsonParser.ParseAsync<TextGenerationStreamResponse>(responseStream, cancellationToken);

    private static StreamingTextContent GetStreamingTextContentFromStreamResponse(TextGenerationStreamResponse response, string modelId)

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

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    private static List<TextContent> GetTextContentsFromResponse(TextGenerationResponse response, string modelId)
After:
    private static List<TextContent> GetTextContentsFromResponse(TextGenerationResponse response, string modelId)
*/


    private static List<TextContent> GetTextContentsFromResponse(TextGenerationResponse response, string modelId)

        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8, new HuggingFaceTextGenerationMetadata(response))).ToList();

    private static List<TextContent> GetTextContentsFromResponse(ImageToTextGenerationResponse response, string modelId)

        => response.Select(r => new TextContent(r.GeneratedText, modelId, r, Encoding.UTF8)).ToList();

    private void LogTextGenerationUsage(HuggingFacePromptExecutionSettings executionSettings)

    {
        if (this.Logger.IsEnabled(LogLevel.Debug))

        {
            this.Logger.LogDebug(

                "HuggingFace text generation usage: ModelId: {ModelId}",

                executionSettings.ModelId ?? this.ModelId);

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }

    }
After:
        }
    }
*/
        }
    }

    private Uri GetTextGenerationEndpoint(string modelId)

        => new($"{this.Endpoint}{this.Separator}models/{modelId}");


/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #endregion
After:
    #endregion
*/

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #region Embeddings
After:
    #region Embeddings
*/
    #endregion

    #region Embeddings
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
After:
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
*/


    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(

        IList<string> data,

        Kernel? kernel,

        CancellationToken cancellationToken)

    {
        var endpoint = this.GetEmbeddingGenerationEndpoint(this.ModelId);

        if (data.Count > 1)

        {
            throw new NotSupportedException("Currently this interface does not support multiple embeddings results per data item, use only one data item");

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        }
After:
        }
*/
        }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
        var request = new TextEmbeddingRequest
After:
        var request = new TextEmbeddingRequest
*/


        var request = new TextEmbeddingRequest

        {
            Inputs = data
        };

        using var httpRequestMessage = this.CreatePost(request, endpoint, this.ApiKey);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)

            .ConfigureAwait(false);

        var response = DeserializeResponse<TextEmbeddingResponse>(body);

        return response.ToList();

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    private Uri GetEmbeddingGenerationEndpoint(string modelId)
After:
    private Uri GetEmbeddingGenerationEndpoint(string modelId)
*/


    private Uri GetEmbeddingGenerationEndpoint(string modelId)

        => new($"{this.Endpoint}{this.Separator}pipeline/feature-extraction/{modelId}");


/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #endregion
After:
    #endregion
*/

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #region Image to Text
After:
    #region Image to Text
*/
    #endregion

    #region Image to Text
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    public async Task<IReadOnlyList<TextContent>> GenerateTextFromImageAsync(ImageContent content, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
After:
    public async Task<IReadOnlyList<TextContent>> GenerateTextFromImageAsync(ImageContent content, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
*/


    public async Task<IReadOnlyList<TextContent>> GenerateTextFromImageAsync(ImageContent content, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)

    {
        using var httpRequestMessage = this.CreateImageToTextRequest(content, executionSettings);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)

            .ConfigureAwait(false);

        var response = DeserializeResponse<ImageToTextGenerationResponse>(body);

        var textContents = GetTextContentsFromResponse(response, executionSettings?.ModelId ?? this.ModelId);

        return textContents;

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    private HttpRequestMessage CreateImageToTextRequest(ImageContent content, PromptExecutionSettings? executionSettings)
After:
    private HttpRequestMessage CreateImageToTextRequest(ImageContent content, PromptExecutionSettings? executionSettings)
*/


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

/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    }
After:
    }
*/
    }
/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    private Uri GetImageToTextGenerationEndpoint(string modelId)
After:
    private Uri GetImageToTextGenerationEndpoint(string modelId)
*/


    private Uri GetImageToTextGenerationEndpoint(string modelId)

        => new($"{this.Endpoint}{this.Separator}models/{modelId}");


/* Unmerged change from project 'Connectors.HuggingFace(netstandard2.0)'
Before:
    #endregion
After:
    #endregion
*/
    #endregion

}
