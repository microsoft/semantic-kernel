// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Contents;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// AssemblyAI speech-to-text service.
/// </summary>
[Experimental("SKEXP0033")]
public sealed class AssemblyAIAudioToTextService : IAudioToTextService
{
    private const string BaseUrl = "https://api.assemblyai.com/";
    private readonly string _apiKey;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Attributes is not used by AssemblyAIAudioToTextService.
    /// </summary>
    public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();

    /// <summary>
    /// Creates an instance of the <see cref="AssemblyAIAudioToTextService"/> with an AssemblyAI API key.
    /// </summary>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="httpClient"></param>
    public AssemblyAIAudioToTextService(
        string apiKey,
        HttpClient httpClient
    )
    {
        this._apiKey = apiKey;
        this._httpClient = httpClient;
    }

    /// <inheritdoc />
    public async Task<TextContent> GetTextContentAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string uploadUrl;
        if (content.AudioUrl is not null)
        {
            // to prevent unintentional file uploads by injection attack
            if (content.AudioUrl.IsFile)
            {
                throw new ArgumentException("File URI is not allowed. Use `AudioContent.Stream` or `AudioContent.File` to transcribe a local file instead.");
            }

            uploadUrl = content.AudioUrl.ToString();
        }
        else if (content.AudioFile is not null)
        {
            using var stream = content.AudioFile.OpenRead();
            uploadUrl = await this.UploadFileAsync(stream, cancellationToken).ConfigureAwait(false);
        }
        else if (content.Data is not null)
        {
            using var stream = content.Data!.ToStream();
            uploadUrl = await this.UploadFileAsync(stream, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            throw new ArgumentException("AudioContent doesn't have any content.", nameof(content));
        }

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return new TextContent(
            text: transcript.RootElement.GetProperty("text").GetString(),
            modelId: null,
            // TODO: change to typed object when AAI SDK is shipped
            innerContent: transcript,
            encoding: Encoding.UTF8,
            metadata: null
        );
    }

    /// <summary>
    /// Transcribe audio file.
    /// </summary>
    /// <param name="content">Stream of the audio file</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text content from audio content.</returns>
    public async Task<TextContent> GetTextContentAsync(
        AudioStreamContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string uploadUrl = await this.UploadFileAsync(content.Stream, cancellationToken).ConfigureAwait(false);

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return new TextContent(
            text: transcript.RootElement.GetProperty("text").GetString(),
            modelId: null,
            // TODO: change to typed object when AAI SDK is shipped
            innerContent: transcript,
            encoding: Encoding.UTF8,
            metadata: null
        );
    }

    private async Task<string> UploadFileAsync(Stream audioStream, CancellationToken ct)
    {
        var url = this.Url("v2/upload");
        using var content = new StreamContent(audioStream);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        using var request = new HttpRequestMessage(HttpMethod.Post, url);
        this.AddDefaultHeaders(request);
        request.Content = content;
        using var response = await this.SendWithSuccessCheckAsync(this._httpClient, request, ct).ConfigureAwait(false);
        var jsonStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
        var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        return json.RootElement.GetProperty("upload_url").GetString()
               ?? throw new KernelException("Property 'upload_url' expected but not found.");
    }

    private async Task<string> CreateTranscriptAsync(
        string audioUrl,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken ct = default
    )
    {
        var url = this.Url("v2/transcript");
        var jsonRequest = new JsonObject();
        jsonRequest["audio_url"] = audioUrl;
        if (executionSettings?.ExtensionData is not null)
        {
            foreach (var attribute in executionSettings.ExtensionData)
            {
                jsonRequest[attribute.Key] = JsonValue.Create(attribute.Value);
            }
        }

        using var request = HttpRequest.CreatePostRequest(url, jsonRequest);
        this.AddDefaultHeaders(request);
        using var response = await this.SendWithSuccessCheckAsync(this._httpClient, request, ct).ConfigureAwait(false);
        var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
        var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        if (json.RootElement.TryGetProperty("error", out var property))
        {
            throw new KernelException($"Failed to create transcript. Reason: {property.GetString()!}");
        }

        return json.RootElement.GetProperty("id").GetString()!;
    }

    private async Task<JsonDocument> WaitForTranscriptToProcessAsync(
        string transcriptId,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken ct = default
    )
    {
        var url = this.Url($"v2/transcript/{transcriptId}");
        var pollingInterval = TimeSpan.FromSeconds(1);
        if (executionSettings is AssemblyAIAudioToTextExecutionSettings aaiSettings)
        {
            pollingInterval = aaiSettings.PollingInterval;
        }

        while (!ct.IsCancellationRequested)
        {
            using var request = HttpRequest.CreateGetRequest(url);
            this.AddDefaultHeaders(request);
            using var response = await this.SendWithSuccessCheckAsync(this._httpClient, request, ct).ConfigureAwait(false);
            var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
            var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);

            var status = json.RootElement.GetProperty("status").GetString()!;
            switch (status)
            {
                case "processing":
                case "queued":
                    await Task.Delay(pollingInterval, ct).ConfigureAwait(false);
                    break;
                case "completed":
                    return json;
                case "error":
                    var errorString = json.RootElement.GetProperty("error").GetString()!;
                    throw new KernelException($"Failed to create transcript. Reason: {errorString}");
                default:
                    throw new KernelException("Unexpected transcript status. This code shouldn't be reachable.");
            }
        }

        ct.ThrowIfCancellationRequested();
        throw new KernelException("This code is unreachable.");
    }

    /// <summary>
    /// Create a URL string that includes the default BaseUrl if the BaseAddress on _httpClient isn't set.
    /// </summary>
    /// <param name="url">URL without base.</param>
    /// <returns>URL with or without BaseUrl.</returns>
    private string Url(string url)
    {
        return this._httpClient.BaseAddress is null ? $"{BaseUrl}{url}" : url;
    }

    private void AddDefaultHeaders(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue(this._apiKey);
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AssemblyAIAudioToTextService)));
    }

    private async Task<HttpResponseMessage> SendWithSuccessCheckAsync(HttpClient client, HttpRequestMessage request, CancellationToken ct)
    {
        HttpResponseMessage? response = null;
        try
        {
            response = await client.SendAsync(request, HttpCompletionOption.ResponseContentRead, ct).ConfigureAwait(false);
        }
        catch (HttpRequestException e)
        {
            throw new HttpOperationException(HttpStatusCode.BadRequest, null, e.Message, e);
        }

        if (response.IsSuccessStatusCode)
        {
            return response;
        }

        string? responseContent = null;
        try
        {
            // On .NET Framework, EnsureSuccessStatusCode disposes of the response content;
            // that was changed years ago in .NET Core, but for .NET Framework it means in order
            // to read the response content in the case of failure, that has to be
            // done before calling EnsureSuccessStatusCode.
            responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            if (response.Content.Headers.ContentType.MediaType == "application/json")
            {
                var json = JsonDocument.Parse(responseContent);
                if (json.RootElement.TryGetProperty("error", out var errorProperty))
                {
                    throw new HttpOperationException(
                        statusCode: response.StatusCode,
                        responseContent: responseContent,
                        message: errorProperty.GetString()!,
                        innerException: null
                    );
                }
            }

            response.EnsureSuccessStatusCode(); // will always throw
        }
        catch (Exception e)
        {
            throw new HttpOperationException(response.StatusCode, responseContent, e.Message, e);
        }

        throw new KernelException("Unreachable code.");
    }
}
