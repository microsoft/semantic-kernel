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
[Experimental("SKEXP0010")]
[Obsolete("Use OpenAI SDK or AzureOpenAI SDK clients for file operations. This class is deprecated and will be removed in a future version.")]
[ExcludeFromCodeCoverage]
public sealed class OpenAIFileService
{
    private const string OrganizationKey = "Organization";
    private const string HeaderNameAuthorization = "Authorization";
    private const string HeaderNameAzureApiKey = "api-key";
    private const string HeaderNameOpenAIAssistant = "OpenAI-Beta";
    private const string HeaderNameUserAgent = "User-Agent";
    private const string HeaderOpenAIValueAssistant = "assistants=v1";
    private const string OpenAIApiEndpoint = "https://api.openai.com/v1/";
    private const string OpenAIApiRouteFiles = "files";
    private const string AzureOpenAIApiRouteFiles = "openai/files";
    private const string AzureOpenAIDefaultVersion = "2024-02-15-preview";

    private readonly string _apiKey;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly Uri _serviceUri;
    private readonly string? _version;
    private readonly string? _organization;

    /// <summary>
    /// Create an instance of the Azure OpenAI chat completion connector
    /// </summary>
    /// <param name="endpoint">Azure Endpoint URL</param>
    /// <param name="apiKey">Azure OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="version">The API version to target.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIFileService(
        Uri endpoint,
        string apiKey,
        string? organization = null,
        string? version = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(apiKey, nameof(apiKey));

        this._apiKey = apiKey;
        this._logger = loggerFactory?.CreateLogger(typeof(OpenAIFileService)) ?? NullLogger.Instance;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._serviceUri = new Uri(this._httpClient.BaseAddress ?? endpoint, AzureOpenAIApiRouteFiles);
        this._version = version ?? AzureOpenAIDefaultVersion;
        this._organization = organization;
    }

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
    public async Task<BinaryContent> GetFileContentAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));
        var contentUri = $"{this._serviceUri}/{id}/content";
        var (stream, mimetype) = await this.StreamGetRequestAsync(contentUri, cancellationToken).ConfigureAwait(false);

        using (stream)
        {
            using var memoryStream = new MemoryStream();
#if NET8_0_OR_GREATER
            await stream.CopyToAsync(memoryStream, cancellationToken).ConfigureAwait(false);
#else
            const int DefaultCopyBufferSize = 81920;
            await stream.CopyToAsync(memoryStream, DefaultCopyBufferSize, cancellationToken).ConfigureAwait(false);
#endif
            return
                new(memoryStream.ToArray(), mimetype)
                {
                    Metadata = new Dictionary<string, object?>() { { "id", id } },
                    Uri = new Uri(contentUri),
                };
        }
    }

    /// <summary>
    /// Retrieve metadata for a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata associated with the specified file identifier.</returns>
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
    /// <returns>The metadata of all uploaded files.</returns>
    public Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default)
        => this.GetFilesAsync(null, cancellationToken);

    /// <summary>
    /// Retrieve metadata for previously uploaded files
    /// </summary>
    /// <param name="filePurpose">The purpose of the files by which to filter.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    public async Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(OpenAIFilePurpose? filePurpose, CancellationToken cancellationToken = default)
    {
        var serviceUri = filePurpose.HasValue && !string.IsNullOrEmpty(filePurpose.Value.Label) ? $"{this._serviceUri}?purpose={filePurpose}" : this._serviceUri.ToString();
        var result = await this.ExecuteGetRequestAsync<FileInfoList>(serviceUri, cancellationToken).ConfigureAwait(false);

        return result.Data.Select(this.ConvertFileReference).ToArray();
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
        Verify.NotNull(fileContent.Data, nameof(fileContent.Data));

        using var formData = new MultipartFormDataContent();
        using var contentPurpose = new StringContent(settings.Purpose.Label);
        using var contentFile = new ByteArrayContent(fileContent.Data.Value.ToArray());
        formData.Add(contentPurpose, "purpose");
        formData.Add(contentFile, "file", settings.FileName);

        var result = await this.ExecutePostRequestAsync<FileInfo>(this._serviceUri.ToString(), formData, cancellationToken).ConfigureAwait(false);

        return this.ConvertFileReference(result);
    }

    private async Task ExecuteDeleteRequestAsync(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateDeleteRequest(this.PrepareUrl(url));
        this.AddRequestHeaders(request);
        using var _ = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private async Task<TModel> ExecuteGetRequestAsync<TModel>(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateGetRequest(this.PrepareUrl(url));
        this.AddRequestHeaders(request);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        var model = JsonSerializer.Deserialize<TModel>(body);

        return
            model ??
            throw new KernelException($"Unexpected response from {url}")
            {
                Data = { { "ResponseData", body } },
            };
    }

    private async Task<(Stream Stream, string? MimeType)> StreamGetRequestAsync(string url, CancellationToken cancellationToken)
    {
        using var request = HttpRequest.CreateGetRequest(this.PrepareUrl(url));
        this.AddRequestHeaders(request);
        var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        try
        {
            return
                (new HttpResponseStream(
                    await response.Content.ReadAsStreamAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false),
                    response),
                    response.Content.Headers.ContentType?.MediaType);
        }
        catch
        {
            response.Dispose();
            throw;
        }
    }

    private async Task<TModel> ExecutePostRequestAsync<TModel>(string url, HttpContent payload, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, this.PrepareUrl(url)) { Content = payload };
        this.AddRequestHeaders(request);
        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        var model = JsonSerializer.Deserialize<TModel>(body);

        return
            model ??
            throw new KernelException($"Unexpected response from {url}")
            {
                Data = { { "ResponseData", body } },
            };
    }

    private string PrepareUrl(string url)
    {
        if (string.IsNullOrWhiteSpace(this._version))
        {
            return url;
        }

        return $"{url}?api-version={this._version}";
    }

    private void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add(HeaderNameOpenAIAssistant, HeaderOpenAIValueAssistant);
        request.Headers.Add(HeaderNameUserAgent, HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIFileService)));

        if (!string.IsNullOrWhiteSpace(this._version))
        {
            // Azure OpenAI
            request.Headers.Add(HeaderNameAzureApiKey, this._apiKey);
            return;
        }

        // OpenAI
        request.Headers.Add(HeaderNameAuthorization, $"Bearer {this._apiKey}");

        if (!string.IsNullOrEmpty(this._organization))
        {
            this._httpClient.DefaultRequestHeaders.Add(OrganizationKey, this._organization);
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
                Purpose = new(result.Purpose),
            };
    }

    private sealed class FileInfoList
    {
        [JsonPropertyName("data")]
        public FileInfo[] Data { get; set; } = [];

        [JsonPropertyName("object")]
        public string Object { get; set; } = "list";
    }

    private sealed class FileInfo
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
