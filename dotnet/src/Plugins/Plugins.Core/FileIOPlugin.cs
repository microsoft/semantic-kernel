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
public sealed class FileIOPlugin
{
    /// <summary>
    /// List of allowed folders to read from or write to.
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
    private HashSet<string>? _allowedFolders;

    /// <summary>
    /// If a list of allowed folder has been provided, the folder of the provided path is checked
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
