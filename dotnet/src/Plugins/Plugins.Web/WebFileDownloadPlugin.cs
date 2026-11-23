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
/// Downloads are denied by default. Configure <see cref="AllowedFolders"/> and
/// <see cref="AllowedOrigins"/> before downloading.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedOrigins"/> and <see cref="AllowedFolders"/> are restricted to trusted
/// values only. Unrestricted configuration may allow unintended downloads to
/// local paths.
/// </para>
/// <para>
/// The default HTTP client does not follow redirects to prevent bypassing the allow-list.
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
        this(HttpClientProvider.GetNonRedirectingHttpClient(), loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WebFileDownloadPlugin"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// When providing a custom client, configure it with <c>AllowAutoRedirect = false</c> to preserve the origin restrictions.
    /// </remarks>
    public WebFileDownloadPlugin(HttpClient httpClient, ILoggerFactory? loggerFactory = null)
    {
        this._httpClient = httpClient;
        this._logger = loggerFactory?.CreateLogger(typeof(WebFileDownloadPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Gets or sets the allowed combinations of scheme, host, and port for downloads.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Defaults to an empty collection. A <see langword="null"/> or empty collection denies all downloads.
    /// Reading this property returns a read-only snapshot with one entry per origin.
    /// </para>
    /// <para>
    /// Each origin must be an absolute HTTP or HTTPS URI, such as <c>https://api.example.com:8443</c>,
    /// without credentials, a resource path, a query, or a fragment.
    /// An omitted port means 80 for HTTP or 443 for HTTPS.
    /// </para>
    /// <para>
    /// Scheme and host comparisons ignore case. All resource paths on a matching origin are permitted.
    /// <see cref="AllowedFolders"/> must still permit the destination file path.
    /// </para>
    /// </remarks>
    /// <exception cref="ArgumentException">An entry is not a valid HTTP or HTTPS origin.</exception>
    public IEnumerable<Uri>? AllowedOrigins
    {
        get => this._allowedOrigins is { } origins ? new List<Uri>(origins).AsReadOnly() : null;
        set => this._allowedOrigins = HttpOriginAllowList.Create(value, nameof(this.AllowedOrigins));
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

        var expandedFilePath = CanonicalizePath(filePath);
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
        using FileStream destination = this.OpenDestination(expandedFilePath, fileMode);

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
    private HashSet<Uri>? _allowedOrigins = [];
    private HashSet<string>? _allowedFolders = [];

    private FileStream OpenDestination(string path, FileMode mode)
    {
        try
        {
            return SecureFileSystem.OpenWrite(path, this._allowedFolders, out _, mode, FileShare.None);
        }
        catch (SecureFileSystem.FileAlreadyExistsException ex)
        {
            throw new InvalidOperationException("Overwriting existing files is disabled.", ex);
        }
    }

    /// <summary>
    /// Checks whether the request destination matches an allowed origin.
    /// </summary>
    /// <param name="uri">The request URI to check.</param>
    /// <returns><see langword="true"/> if the destination is permitted; otherwise, <see langword="false"/>.</returns>
    private bool IsUriAllowed(Uri uri)
    {
        Verify.NotNull(uri);

        return HttpOriginAllowList.Contains(this._allowedOrigins, uri);
    }

    private static string CanonicalizePath(string path)
    {
        var fullPath = SecureFileSystem.NormalizePath(path, expandEnvironmentVariables: true);
        return PathUtilities.GetSafeFullPath(fullPath);
    }

    private static bool IsUncOrExtendedPath(string path) =>
        path.Length >= 2 &&
        (path[0] is '/' or '\\') &&
        (path[1] is '/' or '\\');

    /// <summary>
    /// If a list of allowed folder has been provided, the folder of the provided filePath is checked
    /// to verify it is in the allowed folder list. Paths are canonicalized before comparison.
    /// Subdirectories of allowed folders are also permitted.
    /// </summary>
    private bool IsFilePathAllowed(string path)
    {
        Verify.NotNullOrWhiteSpace(path);

        if (IsUncOrExtendedPath(path))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }

        string? directoryPath = Path.GetDirectoryName(path);

        if (string.IsNullOrEmpty(directoryPath))
        {
            throw new ArgumentException("Invalid file path, a fully qualified file location must be specified.", nameof(path));
        }

        if (this._allowedFolders is null || this._allowedFolders.Count == 0)
        {
            return false;
        }

        var canonicalDir = PathUtilities.GetSafeFullPath(directoryPath);

        foreach (var allowedFolder in this._allowedFolders)
        {
            var canonicalAllowed = PathUtilities.GetSafeFullPath(allowedFolder);
            var separator = Path.DirectorySeparatorChar.ToString();
            if (!canonicalAllowed.EndsWith(separator, PathUtilities.PathComparison))
            {
                canonicalAllowed += separator;
            }

            if (canonicalDir.StartsWith(canonicalAllowed, PathUtilities.PathComparison)
                || (canonicalDir + separator).Equals(canonicalAllowed, PathUtilities.PathComparison))
            {
                return true;
            }
        }

        return false;
    }
    #endregion
}
