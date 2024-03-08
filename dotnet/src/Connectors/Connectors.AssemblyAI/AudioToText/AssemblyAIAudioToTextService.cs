// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// AssemblyAI speech-to-text service.
/// </summary>
public sealed class AssemblyAIAudioToTextService : IAudioToTextService
{
    private const string FallbackBaseUrl = "https://api.assemblyai.com/";
    internal string ApiKey { get; }
    internal HttpClient HttpClient { get; }

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
        HttpClient? httpClient = null
    )
    {
        this.ApiKey = apiKey;
        this.HttpClient = HttpClientProvider.GetHttpClient(httpClient);
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    )
    {
        Verify.NotNull(content);

        string uploadUrl;
        if (content.Data is { IsEmpty: false })
        {
            uploadUrl = await this.UploadFileAsync(content.Data.Value, cancellationToken).ConfigureAwait(false);
        }
        else if (content.Uri is not null)
        {
            // to prevent unintentional file uploads by injection attack
            if (content.Uri.IsFile)
            {
                throw new ArgumentException("File URI is not allowed. Use `AudioContent.Stream` or `AudioContent.File` to transcribe a local file instead.");
            }

            uploadUrl = content.Uri.ToString();
        }
        else
        {
            throw new ArgumentException("AudioContent doesn't have any content.", nameof(content));
        }

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return new[]
        {
            new TextContent(
                text: transcript.RootElement.GetProperty("text").GetString(),
                modelId: null,
                // TODO: change to typed object when AAI SDK is shipped
                innerContent: transcript,
                encoding: Encoding.UTF8,
                metadata: null
            )
        };
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        AudioStreamContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    )
    {
        Verify.NotNull(content);
        Verify.NotNull(content.Stream);

        string uploadUrl = await this.UploadFileAsync(content.Stream, cancellationToken).ConfigureAwait(false);

        var transcriptId = await this.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this.WaitForTranscriptToProcessAsync(transcriptId, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return new[]
        {
            new TextContent(
                text: transcript.RootElement.GetProperty("text").GetString(),
                modelId: null,
                // TODO: change to typed object when AAI SDK is shipped
                innerContent: transcript,
                encoding: Encoding.UTF8,
                metadata: null
            )
        };
    }

    private async Task<string> UploadFileAsync(ReadOnlyMemory<byte> audio, CancellationToken ct)
    {
        // Update to use ReadOnlyMemoryContent if library supports .NET Standard 2.1
        using var content = new ByteArrayContent(audio.ToArray());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        return await this.UploadFileAsync(content, ct).ConfigureAwait(false);
    }

    private async Task<string> UploadFileAsync(Stream audioStream, CancellationToken ct)
    {
        using var content = new StreamContent(audioStream);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        return await this.UploadFileAsync(content, ct).ConfigureAwait(false);
    }

    private async Task<string> UploadFileAsync(HttpContent httpContent, CancellationToken ct)
    {
        var url = this.CreateUrl("v2/upload");

        using var request = new HttpRequestMessage(HttpMethod.Post, url);
        this.AddDefaultHeaders(request);
        request.Content = httpContent;

        using var response = await this.HttpClient.SendWithSuccessCheckAsync(request, ct).ConfigureAwait(false);
        using var jsonStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);

        var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        return json.RootElement.GetProperty("upload_url").GetString()
               ?? throw new KernelException("Property 'upload_url' expected but not found.");
    }

    private async Task<string> CreateTranscriptAsync(
        string audioUrl,
        PromptExecutionSettings? executionSettings,
        CancellationToken ct
    )
    {
        var url = this.CreateUrl("v2/transcript");

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

        using var response = await this.HttpClient.SendWithSuccessCheckAsync(request, ct).ConfigureAwait(false);
        using var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);

        using var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        if (json.RootElement.TryGetProperty("error", out var property))
        {
            throw new KernelException($"Failed to create transcript. Reason: {property.GetString()!}");
        }

        return json.RootElement.GetProperty("id").GetString()!;
    }

    private async Task<JsonDocument> WaitForTranscriptToProcessAsync(
        string transcriptId,
        PromptExecutionSettings? executionSettings,
        CancellationToken ct
    )
    {
        var url = this.CreateUrl($"v2/transcript/{transcriptId}");

        var pollingInterval = TimeSpan.FromMilliseconds(500);
        if (executionSettings is AssemblyAIAudioToTextExecutionSettings aaiSettings)
        {
            pollingInterval = aaiSettings.PollingInterval;
        }

        while (true)
        {
            ct.ThrowIfCancellationRequested();

            using var request = HttpRequest.CreateGetRequest(url);
            this.AddDefaultHeaders(request);

            using var response = await this.HttpClient.SendWithSuccessCheckAsync(request, ct).ConfigureAwait(false);
            using var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);

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
                    throw new KernelException($"Received unexpected transcript status '{status}'.");
            }
        }
    }

    /// <summary>
    /// Create a URL string that includes the default BaseUrl if the BaseAddress on HttpClient isn't set.
    /// </summary>
    /// <param name="url">URL without base.</param>
    /// <returns>URL with or without BaseUrl.</returns>
    private string CreateUrl(string url)
    {
        return this.HttpClient.BaseAddress is null ? $"{FallbackBaseUrl}{url}" : url;
    }

    private void AddDefaultHeaders(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue(this.ApiKey);
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AssemblyAIAudioToTextService)));
    }
}
