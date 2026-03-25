// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// Read and write from a file.
/// </summary>
/// <remarks>
/// <para>
/// This plugin is secure by default. <see cref="AllowedFolders"/> must be explicitly configured
/// before any file operations are permitted. By default, all file paths are denied.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedFolders"/> is restricted to trusted values only.
/// </para>
/// </remarks>
public sealed class FileIOPlugin
{
    /// <summary>
    /// List of allowed folders to read from or write to. Subdirectories of allowed folders are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no folders allowed). Must be explicitly populated
    /// with trusted directory paths before any file operations will succeed.
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
    /// Read a file
    /// </summary>
    /// <example>
    /// {{file.readAsync $path }} => "hello world"
    /// </example>
    /// <param name="path"> Source file </param>
    /// <returns> File content </returns>
    [KernelFunction, Description("Read a file")]
    public async Task<string> ReadAsync([Description("Source file")] string path)
    {
        if (!this.IsFilePathAllowed(path))
        {
            throw new InvalidOperationException("Reading from the provided location is not allowed.");
        }

        using var reader = File.OpenText(path);
        return await reader.ReadToEndAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Write a file
    /// </summary>
    /// <example>
    /// {{file.writeAsync}}
    /// </example>
    /// <param name="path">The destination file path</param>
    /// <param name="content">The file content to write</param>
    /// <returns> An awaitable task </returns>
    [KernelFunction, Description("Write a file")]
    public async Task WriteAsync(
        [Description("Destination file")] string path,
        [Description("File content")] string content)
    {
        if (!this.IsFilePathAllowed(path))
        {
            throw new InvalidOperationException("Writing to the provided location is not allowed.");
        }

        if (this.DisableFileOverwrite && File.Exists(path))
        {
            throw new InvalidOperationException("Overwriting existing files is disabled.");
        }

        byte[] text = Encoding.UTF8.GetBytes(content);
        var fileMode = this.DisableFileOverwrite ? FileMode.CreateNew : FileMode.Create;
        using var writer = new FileStream(path, fileMode, FileAccess.Write, FileShare.None);
        await writer.WriteAsync(text
#if !NET
            , 0, text.Length
#endif
            ).ConfigureAwait(false);
    }

    #region private
    private HashSet<string>? _allowedFolders = [];

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
