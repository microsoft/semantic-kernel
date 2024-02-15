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
/// File service access for OpenAI: https://api.openai.com/v1/files
/// </summary>
[Experimental("SKEXP0015")]
public sealed class OpenAIFileService
{
    private const string OpenAIApiEndpoint = "https://api.openai.com/v1/";
    private const string OpenAIApiRouteFiles = "files";

    private readonly string _apiKey;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly Uri _serviceUri;
    private readonly string? _organization;

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
        this._logger = loggerFactory?.CreateLogger(typeof(OpenAIFileService)) ?? NullLogger.Instance;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._serviceUri = new Uri(this._httpClient.BaseAddress ?? new Uri(OpenAIApiEndpoint), OpenAIApiRouteFiles);
        this._organization = organization;
    }

    /// <summary>
    /// Remove a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task DeleteFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        await this.ExecuteDeleteRequestAsync($"{this._serviceUri}/{id}", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieve the file content from a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file content as <see cref="BinaryContent"/></returns>
    /// <remarks>
    /// Files uploaded with <see cref="OpenAIFilePurpose.Assistants"/> do not support content retrieval.
    /// </remarks>
    public BinaryContent GetFileContent(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        return new BinaryContent(() => this.StreamGetRequestAsync($"{this._serviceUri}/{id}/content", cancellationToken));
    }

    /// <summary>
    /// Retrieve metadata for a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Thet metadata associated with the specified file identifier.</returns>
    public async Task<OpenAIFileReference> GetFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        var result = await this.ExecuteGetRequestAsync<FileInfo>($"{this._serviceUri}/{id}", cancellationToken).ConfigureAwait(false);

        return this.ConvertFileReference(result);
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Thet metadata of all uploaded files.</returns>
    public async Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default)
    {
        var result = await this.ExecuteGetRequestAsync<FileInfoList>(this._serviceUri.ToString(), cancellationToken).ConfigureAwait(false);

        return result.Data.Select(r => this.ConvertFileReference(r)).ToArray();
    }

    /// <summary>
    /// Upload a file.
    /// </summary>
    /// <param name="fileContent">The file content as <see cref="BinaryContent"/></param>
    /// <param name="settings">The upload settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file metadata.</returns>
    public async Task<OpenAIFileReference> UploadContentAsync(BinaryContent fileContent, OpenAIFileUploadExecutionSettings settings, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(settings, nameof(settings));

        using var formData = new MultipartFormDataContent();
        using var contentPurpose = new StringContent(this.ConvertPurpose(settings.Purpose));
        using var contentStream = await fileContent.GetStreamAsync().ConfigureAwait(false);
        using var contentFile = new StreamContent(contentStream);
        formData.Add(contentPurpose, "purpose");
        formData.Add(contentFile, "file", settings.FileName);

        var result = await this.ExecutePostRequestAsync<FileInfo>(this._serviceUri.ToString(), formData, cancellationToken).ConfigureAwait(false);

        return this.ConvertFileReference(result);
    }

    private async Task ExecuteDeleteRequestAsync(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateDeleteRequest(url);
        this.AddRequestHeaders(request);
        using var _ = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private async Task<TModel> ExecuteGetRequestAsync<TModel>(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateGetRequest(url);
        this.AddRequestHeaders(request);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var model = JsonSerializer.Deserialize<TModel>(body);

        return
            model ??
            throw new KernelException($"Unexpected response from {url}")
            {
                Data = { { "ResponseData", body } },
            };
    }

    private async Task<Stream> StreamGetRequestAsync(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateGetRequest(url);
        this.AddRequestHeaders(request);
        var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        try
        {
            return
                new HttpResponseStream(
                    await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false),
                    response);
        }
        catch
        {
            response.Dispose();
            throw;
        }
    }

    private async Task<TModel> ExecutePostRequestAsync<TModel>(string url, HttpContent payload, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, url) { Content = payload };
        this.AddRequestHeaders(request);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var model = JsonSerializer.Deserialize<TModel>(body);

        return
            model ??
            throw new KernelException($"Unexpected response from {url}")
            {
                Data = { { "ResponseData", body } },
            };
    }

    private void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        request.Headers.Add("Authorization", $"Bearer {this._apiKey}");

        if (!string.IsNullOrEmpty(this._organization))
        {
            this._httpClient.DefaultRequestHeaders.Add(OpenAIClientCore.OrganizationKey, this._organization);
        }
    }

    private OpenAIFileReference ConvertFileReference(FileInfo result)
    {
        return
            new OpenAIFileReference
            {
                Id = result.Id,
                FileName = result.FileName,
                CreatedTimestamp = DateTimeOffset.FromUnixTimeSeconds(result.CreatedAt).UtcDateTime,
                SizeInBytes = result.Bytes ?? 0,
                Purpose = this.ConvertPurpose(result.Purpose),
            };
    }

    private OpenAIFilePurpose ConvertPurpose(string purpose) =>
        purpose.ToUpperInvariant() switch
        {
            "ASSISTANTS" => OpenAIFilePurpose.Assistants,
            "FINE-TUNE" => OpenAIFilePurpose.FineTune,
            _ => throw new KernelException($"Unknown {nameof(OpenAIFilePurpose)}: {purpose}."),
        };

    private string ConvertPurpose(OpenAIFilePurpose purpose) =>
        purpose switch
        {
            OpenAIFilePurpose.Assistants => "assistants",
            OpenAIFilePurpose.FineTune => "fine-tune",
            _ => throw new KernelException($"Unknown {nameof(OpenAIFilePurpose)}: {purpose}."),
        };

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
