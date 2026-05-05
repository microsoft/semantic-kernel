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
/// This plugin is secure by default. <see cref="AllowedUploadDirectories"/> must be explicitly configured
/// before any file upload operations are permitted. By default, all local file paths are denied.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedUploadDirectories"/> is restricted to trusted values only.
/// </para>
/// </remarks>
public sealed class CloudDrivePlugin
{
    private readonly ICloudDriveConnector _connector;
    private readonly ILogger _logger;
    private HashSet<string> _allowedUploadDirectories = [];

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

        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));

        var canonicalPath = Path.GetFullPath(Environment.ExpandEnvironmentVariables(filePath));

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
        const string Type = "view"; // TODO expose this as an SK variable
        const string Scope = "anonymous"; // TODO expose this as an SK variable

        return await this._connector.CreateShareLinkAsync(filePath, Type, Scope, cancellationToken).ConfigureAwait(false);
    }

    #region private
    // Use case-insensitive comparison on Windows (case-insensitive FS), case-sensitive on Linux/macOS.
    private static readonly StringComparison s_pathComparison =
        RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    /// <summary>
    /// If a list of allowed upload directories has been provided, the directory of the provided filePath is checked
    /// to verify it is in the allowed directory list. Paths are canonicalized before comparison.
    /// Subdirectories of allowed directories are also permitted.
    /// </summary>
    private bool IsUploadPathAllowed(string path)
    {
        Ensure.NotNullOrWhitespace(path, nameof(path));

        if (path.StartsWith("\\\\", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }

        string? directoryPath = Path.GetDirectoryName(path);

        if (string.IsNullOrEmpty(directoryPath))
        {
            throw new ArgumentException("Invalid file path, a fully qualified file location must be specified.", nameof(path));
        }

        if (this._allowedUploadDirectories.Count == 0)
        {
            return false;
        }

        var canonicalDir = Path.GetFullPath(directoryPath);

        foreach (var allowedDirectory in this._allowedUploadDirectories)
        {
            var canonicalAllowed = Path.GetFullPath(allowedDirectory);
            var separator = Path.DirectorySeparatorChar.ToString();
            if (!canonicalAllowed.EndsWith(separator, s_pathComparison))
            {
                canonicalAllowed += separator;
            }

            if (canonicalDir.StartsWith(canonicalAllowed, s_pathComparison)
                || (canonicalDir + separator).Equals(canonicalAllowed, s_pathComparison))
            {
                return true;
            }
        }

        return false;
    }
    #endregion
}
