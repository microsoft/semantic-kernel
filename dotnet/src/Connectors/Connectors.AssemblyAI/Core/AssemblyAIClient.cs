// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI.Core;

internal sealed class AssemblyAIClient
{
    private readonly Uri _endpoint;
    private readonly string _apiKey;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private const string PublicAPI = "https://api.assemblyai.com/";
    internal AssemblyAIClient(
        HttpClient httpClient,
        string? apiKey,
        Uri? endpoint = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        Verify.NotNull(httpClient);

        endpoint ??= new Uri(PublicAPI);
        this._endpoint = endpoint;
        this._apiKey = apiKey;
        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
    }

    internal async Task<string> UploadFileAsync(ReadOnlyMemory<byte> audio, CancellationToken ct)
    {
        // Update to use ReadOnlyMemoryContent if library supports .NET Standard 2.1
        using var content = new ByteArrayContent(audio.ToArray());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        return await this.UploadFileAsync(content, ct).ConfigureAwait(false);
    }

    internal async Task<string> UploadFileAsync(Stream audioStream, CancellationToken ct)
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

        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, ct).ConfigureAwait(false);
        using var jsonStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);

        var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        return json.RootElement.GetProperty("upload_url").GetString()
               ?? throw new KernelException("Property 'upload_url' expected but not found.");
    }

    internal async Task<string> CreateTranscriptAsync(
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

        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, ct).ConfigureAwait(false);
        using var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);

        using var json = await JsonDocument.ParseAsync(jsonStream, cancellationToken: ct).ConfigureAwait(false);
        if (json.RootElement.TryGetProperty("error", out var property))
        {
            throw new KernelException($"Failed to create transcript. Reason: {property.GetString()!}");
        }

        return json.RootElement.GetProperty("id").GetString()!;
    }

    /// <summary>
    /// Create a URL string that includes the default BaseUrl if the BaseAddress on HttpClient isn't set.
    /// </summary>
    /// <param name="url">URL without base.</param>
    /// <returns>URL with or without BaseUrl.</returns>
    private string CreateUrl(string url)
    {
        return this._httpClient.BaseAddress is null ? $"{this._endpoint}{url}" : url;
    }

    private void AddDefaultHeaders(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue(this._apiKey);
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(this.GetType()));
    }

    internal async Task<JsonElement> WaitForTranscriptToProcessAsync(
        string transcriptId,
        PromptExecutionSettings? executionSettings,
        CancellationToken ct
    )
    {
        var url = this.CreateUrl($"v2/transcript/{transcriptId}");

        var pollingInterval = executionSettings is AssemblyAIAudioToTextExecutionSettings aaiSettings
            ? aaiSettings.PollingInterval
            : TimeSpan.FromMilliseconds(500);

        while (true)
        {
            ct.ThrowIfCancellationRequested();

            using var request = HttpRequest.CreateGetRequest(url);
            this.AddDefaultHeaders(request);

            using var response = await this._httpClient.SendWithSuccessCheckAsync(request, ct).ConfigureAwait(false);
            using var jsonStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);

            var json = await JsonSerializer.DeserializeAsync<JsonElement>(jsonStream, cancellationToken: ct).ConfigureAwait(false);

            var status = json.GetProperty("status").GetString()!;
            switch (status)
            {
                case "processing":
                case "queued":
                    await Task.Delay(pollingInterval, ct).ConfigureAwait(false);
                    break;
                case "completed":
                    return json;
                case "error":
                    var errorString = json.GetProperty("error").GetString()!;
                    throw new KernelException($"Failed to create transcript. Reason: {errorString}");
                default:
                    throw new KernelException($"Received unexpected transcript status '{status}'.");
            }
        }
    }
}
