// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Buffers;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Web;

/// <summary>
/// Plugin to download web files.
/// </summary>
public sealed class WebFileDownloadPlugin
{
    /// <summary>
    /// Plugin parameter: where to save file.
    /// </summary>
    public const string FilePathParamName = "filePath";

    /// <summary>
    /// Initializes a new instance of the <see cref="WebFileDownloadPlugin"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public WebFileDownloadPlugin(ILoggerFactory? loggerFactory = null) :
        this(HttpClientProvider.GetHttpClient(), loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WebFileDownloadPlugin"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public WebFileDownloadPlugin(HttpClient httpClient, ILoggerFactory? loggerFactory = null)
    {
        this._httpClient = httpClient;
        this._logger = loggerFactory?.CreateLogger(typeof(WebFileDownloadPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// List of allowed domains to download from.
    /// </summary>
    public IEnumerable<string>? AllowedDomains
    {
        get => this._allowedDomains;
        set => this._allowedDomains = value is null ? null : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// List of allowed folders to download to.
    /// </summary>
    public IEnumerable<string>? AllowedFolders
    {
        get => this._allowedFolders;
        set => this._allowedFolders = value is null ? null : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Set to true to disable overwriting existing files.
    /// </summary>
    public bool DisableFileOverwrite { get; set; } = false;

    /// <summary>
    /// Set the maximum allowed download size.
    /// </summary>
    public long MaximumDownloadSize { get; set; } = long.MaxValue;

    /// <summary>
    /// Downloads a file to a local file path.
    /// </summary>
    /// <param name="url">URI of file to download</param>
    /// <param name="filePath">Path where to save file locally</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>Task.</returns>
    /// <exception cref="KeyNotFoundException">Thrown when the location where to download the file is not provided</exception>
    [KernelFunction, Description("Downloads a file to local storage")]
    public async Task DownloadToFileAsync(
        [Description("URL of file to download")] Uri url,
        [Description("Path where to save file locally")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug($"{nameof(this.DownloadToFileAsync)} got called");
        this._logger.LogDebug("Sending GET request for {0}", url);

        if (!this.IsUriAllowed(url))
        {
            throw new InvalidOperationException("Downloading from the provided location is not allowed.");
        }

        var expandedFilePath = Environment.ExpandEnvironmentVariables(filePath);
        if (!this.IsFilePathAllowed(expandedFilePath))
        {
            throw new InvalidOperationException("Downloading to the provided location is not allowed.");
        }

        using HttpRequestMessage request = new(HttpMethod.Get, url);

        using HttpResponseMessage response = await this._httpClient.SendWithSuccessCheckAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken).ConfigureAwait(false);

        // Check the content length if provided
        if (response.Content.Headers.ContentLength.HasValue && response.Content.Headers.ContentLength.Value > this.MaximumDownloadSize)
        {
            throw new InvalidOperationException($"The file size exceeds the maximum allowed size of {this.MaximumDownloadSize} bytes.");
        }

        this._logger.LogDebug("Response received: {0}", response.StatusCode);

        var fileMode = this.DisableFileOverwrite ? FileMode.CreateNew : FileMode.Create;

        using Stream source = await response.Content.ReadAsStreamAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false);
        using FileStream destination = new(expandedFilePath, FileMode.Create);

        int bufferSize = 81920;
        byte[] buffer = ArrayPool<byte>.Shared.Rent(81920);
        try
        {
            long totalBytesWritten = 0;
            int bytesRead;
#if NET6_0_OR_GREATER
            while ((bytesRead = await source.ReadAsync(buffer.AsMemory(0, bufferSize), cancellationToken).ConfigureAwait(false)) != 0)
#else
            while ((bytesRead = await source.ReadAsync(buffer, 0, bufferSize, cancellationToken).ConfigureAwait(false)) != 0)
#endif
            {
                if (totalBytesWritten + bytesRead > this.MaximumDownloadSize)
                {
                    throw new InvalidOperationException($"The file size exceeds the maximum allowed size of {this.MaximumDownloadSize} bytes.");
                }
#if NET6_0_OR_GREATER
                await destination.WriteAsync(buffer.AsMemory(0, bytesRead), cancellationToken).ConfigureAwait(false);
#else
                await destination.WriteAsync(buffer, 0, bytesRead, cancellationToken).ConfigureAwait(false);
#endif
                totalBytesWritten += bytesRead;
            }
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);
        }
    }

    #region private
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private HashSet<string>? _allowedDomains;
    private HashSet<string>? _allowedFolders;

    /// <summary>
    /// If a list of allowed domains has been provided, the host of the provided uri is checked
    /// to verify it is in the allowed domain list.
    /// </summary>
    private bool IsUriAllowed(Uri uri)
    {
        Verify.NotNull(uri);

        return this._allowedDomains is null || this._allowedDomains.Contains(uri.Host);
    }

    /// <summary>
    /// If a list of allowed folder has been provided, the folder of the provided filePath is checked
    /// to verify it is in the allowed folder list.
    /// </summary>
    private bool IsFilePathAllowed(string path)
    {
        Verify.NotNullOrWhiteSpace(path);

        if (path.StartsWith("\\\\", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }

        if (this.DisableFileOverwrite && File.Exists(path))
        {
            throw new ArgumentException("Invalid file path, overwriting existing files is disabled.", nameof(path));
        }

        string? directoryPath = Path.GetDirectoryName(path);

        if (string.IsNullOrEmpty(directoryPath))
        {
            throw new ArgumentException("Invalid file path, a fully qualified file location must be specified.", nameof(path));
        }

        if (File.Exists(path) && File.GetAttributes(path).HasFlag(FileAttributes.ReadOnly))
        {
            // Most environments will throw this with OpenWrite, but running inside docker on Linux will not.
            throw new UnauthorizedAccessException($"File is read-only: {path}");
        }

        return this._allowedFolders is null || this._allowedFolders.Contains(directoryPath);
    }
    #endregion
}
