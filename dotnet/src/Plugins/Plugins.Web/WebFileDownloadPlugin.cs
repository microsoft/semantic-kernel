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
/// <remarks>
/// <para>
/// This plugin is secure by default. Both <see cref="AllowedDomains"/> and <see cref="AllowedFolders"/>
/// must be explicitly configured before any downloads are permitted. By default, all domains and all
/// file paths are denied.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedDomains"/> and <see cref="AllowedFolders"/> are restricted to trusted
/// values only. Unrestricted configuration may allow unintended downloads to
/// local paths.
/// </para>
/// </remarks>
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
    /// <remarks>
    /// Defaults to an empty collection (no domains allowed). Must be explicitly populated
    /// with trusted domains before any downloads will succeed.
    /// </remarks>
    public IEnumerable<string>? AllowedDomains
    {
        get => this._allowedDomains;
        set => this._allowedDomains = value is null ? null : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// List of allowed folders to download to. Subdirectories of allowed folders are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no folders allowed). Must be explicitly populated
    /// with trusted directory paths before any downloads will succeed.
    /// Paths are canonicalized before validation to prevent directory traversal.
    /// </remarks>
    public IEnumerable<string>? AllowedFolders
    {
        get => this._allowedFolders;
        set => this._allowedFolders = value is null ? null : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Set to false to allow overwriting existing files.
    /// </summary>
    /// <remarks>
    /// Defaults to <c>true</c> (overwriting is disabled).
    /// </remarks>
    public bool DisableFileOverwrite { get; set; } = true;

    /// <summary>
    /// Set the maximum allowed download size.
    /// </summary>
    /// <remarks>
    /// Defaults to 10 MB.
    /// </remarks>
    public long MaximumDownloadSize { get; set; } = 10 * 1024 * 1024;

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

        var expandedFilePath = Path.GetFullPath(Environment.ExpandEnvironmentVariables(filePath));
        if (!this.IsFilePathAllowed(expandedFilePath))
        {
            throw new InvalidOperationException("Downloading to the provided location is not allowed.");
        }

        if (this.DisableFileOverwrite && File.Exists(expandedFilePath))
        {
            throw new InvalidOperationException("Overwriting existing files is disabled.");
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
        using FileStream destination = new(expandedFilePath, fileMode);

        int bufferSize = 81920;
        byte[] buffer = ArrayPool<byte>.Shared.Rent(81920);
        try
        {
            long totalBytesWritten = 0;
            int bytesRead;
#if NET
            while ((bytesRead = await source.ReadAsync(buffer.AsMemory(0, bufferSize), cancellationToken).ConfigureAwait(false)) != 0)
#else
            while ((bytesRead = await source.ReadAsync(buffer, 0, bufferSize, cancellationToken).ConfigureAwait(false)) != 0)
#endif
            {
                if (totalBytesWritten + bytesRead > this.MaximumDownloadSize)
                {
                    throw new InvalidOperationException($"The file size exceeds the maximum allowed size of {this.MaximumDownloadSize} bytes.");
                }
#if NET
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
    private HashSet<string>? _allowedDomains = [];
    private HashSet<string>? _allowedFolders = [];

    /// <summary>
    /// If a list of allowed domains has been provided, the host of the provided uri is checked
    /// to verify it is in the allowed domain list.
    /// </summary>
    private bool IsUriAllowed(Uri uri)
    {
        Verify.NotNull(uri);

        return this._allowedDomains is not null
            && this._allowedDomains.Count > 0
            && this._allowedDomains.Contains(uri.Host);
    }

    /// <summary>
    /// If a list of allowed folder has been provided, the folder of the provided filePath is checked
    /// to verify it is in the allowed folder list. Paths are canonicalized before comparison.
    /// Subdirectories of allowed folders are also permitted.
    /// </summary>
    private bool IsFilePathAllowed(string path)
    {
        Verify.NotNullOrWhiteSpace(path);

        if (path.StartsWith("\\\\", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
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

        if (this._allowedFolders is null || this._allowedFolders.Count == 0)
        {
            return false;
        }

        var canonicalDir = Path.GetFullPath(directoryPath);

        foreach (var allowedFolder in this._allowedFolders)
        {
            var canonicalAllowed = Path.GetFullPath(allowedFolder);
            var separator = Path.DirectorySeparatorChar.ToString();
            if (!canonicalAllowed.EndsWith(separator, StringComparison.OrdinalIgnoreCase))
            {
                canonicalAllowed += separator;
            }

            if (canonicalDir.StartsWith(canonicalAllowed, StringComparison.OrdinalIgnoreCase)
                || (canonicalDir + separator).Equals(canonicalAllowed, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }
    #endregion
}
