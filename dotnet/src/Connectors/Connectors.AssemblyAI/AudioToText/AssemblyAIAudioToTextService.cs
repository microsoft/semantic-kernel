// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Contents;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// AssemblyAI speech-to-text service.
/// </summary>
[Experimental("SKEXP0005")]
public sealed class AssemblyAIAudioToTextService : IAudioToTextService
{
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

    /// <summary>
    /// Transcribe audio file.
    /// </summary>
    /// <param name="content">Audio content.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text content from audio content.</returns>
    public async Task<TextContent> GetTextContentAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string uploadUrl;
        using var stream = content.Data!.ToStream();
        {
            uploadUrl = await this.UploadFileAsync(stream, cancellationToken).ConfigureAwait(false);
        }

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, cancellationToken)
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
    /// <param name="fileStream">Stream of the audio file</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<TextContent> GetTextContentAsync(
        Stream fileStream,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string uploadUrl = await this.UploadFileAsync(fileStream, cancellationToken).ConfigureAwait(false);

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, cancellationToken)
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
    /// <param name="fileUrl">Public URL of the audio file to transcribe</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<TextContent> GetTextContentAsync(
        Uri fileUrl,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // to prevent unintentional file uploads by injection attack
        if (fileUrl.IsFile)
        {
            throw new ArgumentException("File URI is not allowed. Use `Stream` or `FileInfo` to transcribe a local file instead.");
        }

        var transcriptId = await this.CreateTranscriptAsync(fileUrl.ToString(), executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, cancellationToken)
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
    /// <param name="file">Audio file to transcribe</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<TextContent> GetTextContentAsync(
        FileInfo file,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        string uploadUrl;
        using (var fileStream = file.OpenRead())
        {
            uploadUrl = await this.UploadFileAsync(fileStream, cancellationToken).ConfigureAwait(false);
        }

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, cancellationToken)
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
        const string URL = "https://api.assemblyai.com/v2/upload";
        using var content = new StreamContent(audioStream);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        using var request = new HttpRequestMessage(HttpMethod.Post, URL);
        request.Headers.Authorization = new AuthenticationHeaderValue(this._apiKey);
        request.Content = content;
        using var response = await this._httpClient.SendAsync(request, ct).ConfigureAwait(false);
        await ThrowIfNotSuccessStatusCodeAsync("Failed to upload file.", response, ct)
            .ConfigureAwait(false);
        var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
        var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        return json.RootElement.GetProperty("upload_url").GetString()
               ?? throw new AssemblyAIApiException("Property 'upload_url' expected but not found.");
    }

    private async Task<string> CreateTranscriptAsync(
        string audioUrl,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken ct = default
    )
    {
        const string URL = "https://api.assemblyai.com/v2/transcript";
        var jsonRequest = new JsonObject();
        jsonRequest["audio_url"] = audioUrl;
        if (executionSettings?.ExtensionData is not null)
        {
            foreach (var attribute in executionSettings.ExtensionData)
            {
                jsonRequest[attribute.Key] = JsonValue.Create(attribute.Value);
            }
        }

        using var content = new StringContent(jsonRequest.ToJsonString(), Encoding.UTF8, "application/json");
        using var request = new HttpRequestMessage(HttpMethod.Post, URL);
        request.Headers.Authorization = new AuthenticationHeaderValue(this._apiKey);
        request.Content = content;
        using var response = await this._httpClient.SendAsync(request, ct).ConfigureAwait(false);
        await ThrowIfNotSuccessStatusCodeAsync("Failed to create transcript", response, ct)
            .ConfigureAwait(false);
        var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
        var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        if (json.RootElement.TryGetProperty("error", out var property))
        {
            throw new AssemblyAIApiException($"Failed to create transcript. Reason: {property.GetString()!}");
        }

        return json.RootElement.GetProperty("id").GetString()!;
    }

    private async Task<JsonDocument> WaitForTranscriptToProcessAsync(string transcriptId, CancellationToken ct)
    {
        var url = $"https://api.assemblyai.com/v2/transcript/{transcriptId}";

        while (!ct.IsCancellationRequested)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Authorization = new AuthenticationHeaderValue(this._apiKey);
            using var response = await this._httpClient.SendAsync(request, ct).ConfigureAwait(false);
            await ThrowIfNotSuccessStatusCodeAsync("Error waiting for transcript.", response, ct)
                .ConfigureAwait(false);
            var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
            var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);

            var status = json.RootElement.GetProperty("status").GetString()!;
            switch (status)
            {
                case "processing":
                case "queued":
                    await Task.Delay(TimeSpan.FromSeconds(1), ct).ConfigureAwait(false);
                    break;
                case "completed":
                    return json;
                case "error":
                    var errorString = json.RootElement.GetProperty("error").GetString()!;
                    throw new AssemblyAIApiException($"Failed to create transcript. Reason: {errorString}");
                default:
                    throw new AssemblyAIApiException("Unexpected transcript status. This code shouldn't be reachable.");
            }
        }

        ct.ThrowIfCancellationRequested();
        throw new AssemblyAIApiException("This code is unreachable.");
    }

    private static async Task ThrowIfNotSuccessStatusCodeAsync(
        string errorMessagePrefix,
        HttpResponseMessage response,
        CancellationToken ct
    )
    {
        if (response.IsSuccessStatusCode)
        {
            return;
        }

        if (response.Content.Headers.ContentType.MediaType == "application/json")
        {
            var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
            var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
            if (json.RootElement.TryGetProperty("error", out var property))
            {
                throw new AssemblyAIApiException($"{errorMessagePrefix} Reason: {property.GetString()!}");
            }
        }

        response.EnsureSuccessStatusCode();
    }
}
