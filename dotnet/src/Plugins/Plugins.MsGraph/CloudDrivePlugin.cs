// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Plugins.MsGraph.Diagnostics;

namespace Microsoft.SemanticKernel.Plugins.MsGraph;

/// <summary>
/// Cloud drive plugin (e.g. OneDrive).
/// </summary>
/// <remarks>
/// <para>
/// This plugin is secure by default. <see cref="AllowedUploadDirectories"/>, <see cref="AllowedUploadDestinationPaths"/>,
/// <see cref="AllowedReadPaths"/>, and <see cref="AllowedSharePaths"/> must be explicitly configured
/// before file upload, read, or share-link operations are permitted.
/// By default, all paths are denied.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedUploadDirectories"/>, <see cref="AllowedUploadDestinationPaths"/>, <see cref="AllowedReadPaths"/>,
/// and <see cref="AllowedSharePaths"/> are restricted to trusted values only.
/// </para>
/// </remarks>
public sealed class CloudDrivePlugin
{
    private readonly ICloudDriveConnector _connector;
    private readonly ILogger _logger;
    private HashSet<string> _allowedUploadDirectories = [];
    private HashSet<string> _allowedSharePaths = [];
    private HashSet<string> _allowedReadPaths = [];
    private HashSet<string> _allowedUploadDestinationPaths = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="CloudDrivePlugin"/> class.
    /// </summary>
    /// <param name="connector">The cloud drive connector.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public CloudDrivePlugin(ICloudDriveConnector connector, ILoggerFactory? loggerFactory = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = loggerFactory?.CreateLogger(typeof(CloudDrivePlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// List of allowed local directories from which files may be uploaded. Subdirectories of allowed directories are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no directories allowed). Must be explicitly populated
    /// with trusted directory paths before any file upload operations will succeed.
    /// Paths are canonicalized before validation to prevent directory traversal.
    /// </remarks>
    public IEnumerable<string> AllowedUploadDirectories
    {
        get => this._allowedUploadDirectories;
        set => this._allowedUploadDirectories = value is null ? [] : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// List of allowed remote directory prefixes for which sharing links may be created.
    /// A file is permitted if its parent directory starts with (or equals) any entry in this list.
    /// Subdirectories of allowed paths are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no paths allowed). Must be explicitly populated
    /// with trusted remote directory paths before any share-link operations will succeed.
    /// Paths are normalized with forward slashes and dot-segments are collapsed before comparison.
    /// Matching is case-insensitive (OneDrive paths are case-insensitive).
    /// </remarks>
    public IEnumerable<string> AllowedSharePaths
    {
        get => this._allowedSharePaths;
        set => this._allowedSharePaths = value is null ? [] : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// List of allowed remote directory prefixes from which file contents may be read.
    /// A file is permitted if its parent directory starts with (or equals) any entry in this list.
    /// Subdirectories of allowed paths are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no paths allowed). Must be explicitly populated
    /// with trusted remote directory paths before any read operations will succeed.
    /// Paths are normalized with forward slashes and dot-segments are collapsed before comparison.
    /// Matching is case-insensitive (OneDrive paths are case-insensitive).
    /// </remarks>
    public IEnumerable<string> AllowedReadPaths
    {
        get => this._allowedReadPaths;
        set => this._allowedReadPaths = value is null ? [] : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// List of allowed remote directory prefixes to which files may be uploaded.
    /// A destination is permitted if its parent directory starts with (or equals) any entry in this list.
    /// Subdirectories of allowed paths are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no paths allowed). Must be explicitly populated
    /// with trusted remote directory paths before any upload-destination operations will succeed.
    /// Paths are normalized with forward slashes and dot-segments are collapsed before comparison.
    /// Matching is case-insensitive (OneDrive paths are case-insensitive).
    /// </remarks>
    public IEnumerable<string> AllowedUploadDestinationPaths
    {
        get => this._allowedUploadDestinationPaths;
        set => this._allowedUploadDestinationPaths = value is null ? [] : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Get the contents of a file stored in a cloud drive.
    /// </summary>
    /// <param name="filePath">The path to the file.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>A string containing the file content.</returns>
    [KernelFunction, Description("Get the contents of a file in a cloud drive.")]
    public async Task<string?> GetFileContentAsync(
        [Description("Path to file")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting file content for '{0}'", filePath);

        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));

        if (!this.IsAllowedRemotePath(filePath, this._allowedReadPaths))
        {
            throw new InvalidOperationException("Reading from the provided path is not allowed. Configure 'AllowedReadPaths' with trusted remote paths to enable reading.");
        }

        Stream? fileContentStream = await this._connector.GetFileContentStreamAsync(filePath, cancellationToken).ConfigureAwait(false);

        if (fileContentStream is null)
        {
            this._logger.LogDebug("File content stream for '{0}' is null", filePath);
            return null;
        }

        using StreamReader sr = new(fileContentStream);
        return await sr.ReadToEndAsync(
#if NET
            cancellationToken
#endif
            ).ConfigureAwait(false);
    }

    /// <summary>
    /// Upload a small file to OneDrive (less than 4MB).
    /// </summary>
    /// <param name="filePath">The path to the file.</param>
    /// <param name="destinationPath">The remote path to store the file.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    [KernelFunction, Description("Upload a small file to OneDrive (less than 4MB).")]
    public async Task UploadFileAsync(
        [Description("Path to file")] string filePath,
        [Description("Remote path to store the file")] string destinationPath,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(destinationPath))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(destinationPath));
        }

        if (!this.IsAllowedRemotePath(destinationPath, this._allowedUploadDestinationPaths))
        {
            throw new InvalidOperationException("Uploading to the provided remote destination is not allowed. Configure 'AllowedUploadDestinationPaths' with trusted remote paths to enable uploads.");
        }

        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));

        var canonicalPath = CanonicalizePath(filePath);

        if (!this.IsUploadPathAllowed(canonicalPath))
        {
            throw new InvalidOperationException("Uploading from the provided location is not allowed. Configure 'AllowedUploadDirectories' with trusted directory paths to enable uploads.");
        }

        this._logger.LogDebug("Uploading file '{0}'", canonicalPath);

        // TODO Add support for large file uploads (i.e. upload sessions)
        await this._connector.UploadSmallFileAsync(canonicalPath, destinationPath, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a sharable link to a file stored in a cloud drive.
    /// </summary>
    /// <param name="filePath">The path to the file.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>A string containing the sharable link.</returns>
    [KernelFunction, Description("Create a sharable link to a file stored in a cloud drive.")]
    public async Task<string> CreateLinkAsync(
        [Description("Path to file")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Creating link for '{0}'", filePath);
        const string Type = "view";
        const string Scope = "organization";

        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));

        if (!this.IsAllowedRemotePath(filePath, this._allowedSharePaths))
        {
            throw new InvalidOperationException("Creating a share link for the provided path is not allowed. Configure 'AllowedSharePaths' with trusted remote paths to enable sharing.");
        }

        return await this._connector.CreateShareLinkAsync(filePath, Type, Scope, cancellationToken).ConfigureAwait(false);
    }

    #region private
    // Use case-insensitive comparison on Windows (case-insensitive FS), case-sensitive on Linux/macOS.
    private static readonly StringComparison s_pathComparison =
        RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    /// <summary>
    /// Checks whether the provided remote path falls within one of the allowed remote directory prefixes.
    /// Paths are normalized with forward slashes, dot-segments are collapsed,
    /// and compared case-insensitively (OneDrive paths are case-insensitive).
    /// Subdirectories of allowed paths are permitted.
    /// </summary>
    private bool IsAllowedRemotePath(string path, HashSet<string> allowedPaths)
    {
        Ensure.NotNullOrWhitespace(path, nameof(path));

        if (allowedPaths.Count == 0)
        {
            return false;
        }

        // Normalize to forward slashes and collapse dot-segments to prevent traversal bypass.
        var normalizedPath = NormalizeRemotePath(path);

        foreach (var allowedPath in allowedPaths)
        {
            var normalizedAllowed = NormalizeRemotePath(allowedPath);
            if (!normalizedAllowed.EndsWith("/", StringComparison.Ordinal))
            {
                normalizedAllowed += "/";
            }

            var normalizedDir = normalizedPath;
            int lastSlash = normalizedDir.LastIndexOf('/');
            if (lastSlash >= 0)
            {
                normalizedDir = normalizedDir.Substring(0, lastSlash);
            }

            if ((normalizedDir + "/").StartsWith(normalizedAllowed, StringComparison.OrdinalIgnoreCase)
                || (normalizedDir + "/").Equals(normalizedAllowed, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Normalizes a remote path by replacing backslashes with forward slashes
    /// and collapsing "." and ".." segments to prevent traversal bypass.
    /// </summary>
    private static string NormalizeRemotePath(string path)
    {
        var normalizedPath = path.Replace('\\', '/');

        // Collapse ".." and "." segments to prevent traversal bypass.
        var segments = normalizedPath.Split(new[] { '/' }, StringSplitOptions.RemoveEmptyEntries);
        var stack = new List<string>();
        foreach (var segment in segments)
        {
            if (segment == ".." && stack.Count > 0)
            {
                stack.RemoveAt(stack.Count - 1);
            }
            else if (segment != "." && segment != "..")
            {
                stack.Add(segment);
            }
        }

        return "/" + string.Join("/", stack);
    }

    /// <summary>
    /// Expands environment variables and resolves the path to its canonical form.
    /// This must be called before validation to prevent validate/use mismatches.
    /// </summary>
    private static string CanonicalizePath(string path)
    {
        Ensure.NotNullOrWhitespace(path, nameof(path));

        if (path.StartsWith("\\\\", StringComparison.OrdinalIgnoreCase) ||
            path.StartsWith("//", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }

        // Expand environment variables first, then canonicalize — so that
        // validation and I/O operate on the same resolved path.
        var expanded = Environment.ExpandEnvironmentVariables(path);

        // Re-check after expansion: an env var could have expanded to a UNC
        // or extended-path prefix (e.g., %NETSHARE% → \\server\share).
        if (expanded.StartsWith("\\\\", StringComparison.OrdinalIgnoreCase) ||
            expanded.StartsWith("//", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }

        return Path.GetFullPath(expanded);
    }

    /// <summary>
    /// Checks whether a canonicalized file path falls within one of the allowed upload directories.
    /// Subdirectories of allowed directories are also permitted.
    /// </summary>
    private bool IsUploadPathAllowed(string canonicalPath)
    {
        Ensure.NotNullOrWhitespace(canonicalPath, nameof(canonicalPath));

        string? directoryPath = Path.GetDirectoryName(canonicalPath);

        if (string.IsNullOrEmpty(directoryPath))
        {
            throw new ArgumentException("Invalid file path, a fully qualified file location must be specified.", nameof(canonicalPath));
        }

        if (this._allowedUploadDirectories.Count == 0)
        {
            return false;
        }

        foreach (var allowedDirectory in this._allowedUploadDirectories)
        {
            var canonicalAllowed = Path.GetFullPath(allowedDirectory);
            var separator = Path.DirectorySeparatorChar.ToString();
            if (!canonicalAllowed.EndsWith(separator, s_pathComparison))
            {
                canonicalAllowed += separator;
            }

            if (directoryPath.StartsWith(canonicalAllowed, s_pathComparison)
                || (directoryPath + separator).Equals(canonicalAllowed, s_pathComparison))
            {
                return true;
            }
        }

        return false;
    }
    #endregion
}
