// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Implementation of IFileService for OpenAI: https://api.openai.com/v1/files
/// </summary>
[Experimental("SKEXP0099")]
public sealed class OpenAIFileService
{
    private const string OpenAIApiEndpoint = "https://api.openai.com/v1/files";

    private readonly string _apiKey;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;

    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIFileService(
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(apiKey, nameof(apiKey));

        this._apiKey = apiKey;
        this._logger = loggerFactory?.CreateLogger(typeof(OpenAIChatCompletionService)) ?? NullLogger.Instance;

        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);

        if (!string.IsNullOrEmpty(organization))
        {
            this._httpClient.DefaultRequestHeaders.Add(OpenAIClientCore.OrganizationKey, organization);
        }

        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderValues.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {this._apiKey}");
    }

    /// <inheritdoc/>
    public async Task DeleteFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        await this.ExecuteDeleteRequestAsync($"{OpenAIApiEndpoint}/{id}", cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public BinaryContent GetFileContent(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        return new BinaryContent(() => this.StreamGetRequestAsync($"{OpenAIApiEndpoint}/{id}/content", cancellationToken));
    }

    /// <inheritdoc/>
    public async Task<OpenAIFileReference> GetFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        var result = await this.ExecuteGetRequestAsync<FileInfo>($"{OpenAIApiEndpoint}/{id}", cancellationToken).ConfigureAwait(false);

        return this.Convert(result);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default)
    {
        var result = await this.ExecuteGetRequestAsync<FileInfoList>(OpenAIApiEndpoint, cancellationToken).ConfigureAwait(false);

        return result.Data.Select(r => this.Convert(r)).ToArray();
    }

    /// <inheritdoc/>
    public async Task<OpenAIFileReference> UploadContentAsync(OpenAIFileUploadRequest request, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(request, nameof(request));

        using var formData = new MultipartFormDataContent();
#pragma warning disable CA1308 // Normalize strings to uppercase - OpenAI requires lower case
        using var contentPurpose = new StringContent(request.Purpose.ToString().ToLowerInvariant());
#pragma warning restore CA1308 // Normalize strings to uppercase
        using var contentStream = await request.Content.GetStreamAsync().ConfigureAwait(false);
        using var contentFile = new StreamContent(contentStream);
        formData.Add(contentPurpose, "purpose");
        formData.Add(contentFile, "file", request.FileName);

        var result = await this.ExecutePostRequestAsync<FileInfo>(OpenAIApiEndpoint, formData, cancellationToken).ConfigureAwait(false);

        return this.Convert(result);
    }

    private async Task ExecuteDeleteRequestAsync(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateDeleteRequest(url);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private async Task<TModel> ExecuteGetRequestAsync<TModel>(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateGetRequest(url);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var model = JsonSerializer.Deserialize<TModel>(body);

        if (model is null)
        {
            throw new KernelException($"Unexpected response from {url}")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return model;
    }

    private async Task<Stream> StreamGetRequestAsync(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateGetRequest(url);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        return await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
    }

    private async Task<TModel> ExecutePostRequestAsync<TModel>(string url, HttpContent payload, CancellationToken cancellationToken)
    {
        using var response = await this._httpClient.PostAsync(url, payload, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var model = JsonSerializer.Deserialize<TModel>(body);

        if (model is null)
        {
            throw new KernelException($"Unexpected response from {url}")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return model;
    }

    private OpenAIFileReference Convert(FileInfo result)
    {
        Enum.TryParse<OpenAIFilePurpose>(result.Purpose, ignoreCase: true, out var purpose);

        return
            new OpenAIFileReference
            {
                Id = result.Id,
                FileName = result.FileName,
                CreatedTimestamp = DateTimeOffset.FromUnixTimeSeconds(result.CreatedAt).UtcDateTime,
                SizeInBytes = result.Bytes ?? 0,
                Purpose = purpose,
            };
    }

    private class FileInfoList
    {
        [JsonPropertyName("data")]
        public FileInfo[] Data { get; set; } = Array.Empty<FileInfo>();

        [JsonPropertyName("object")]
        public string Object { get; set; } = "list";
    }

    private class FileInfo
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("object")]
        public string Object { get; set; } = "file";

        [JsonPropertyName("bytes")]
        public int? Bytes { get; set; }

        [JsonPropertyName("created_at")]
        public long CreatedAt { get; set; }

        [JsonPropertyName("filename")]
        public string FileName { get; set; } = string.Empty;

        [JsonPropertyName("purpose")]
        public string Purpose { get; set; } = string.Empty;
    }
}
