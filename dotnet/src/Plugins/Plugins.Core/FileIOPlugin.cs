// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// Read and write from a file.
/// </summary>
public sealed class FileIOPlugin
{
    /// <summary>
    /// Read a file
    /// </summary>
    /// <example>
    /// {{file.readAsync $path }} => "hello world"
    /// </example>
    /// <param name="path"> Source file </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns> File content </returns>
    [KernelFunction, Description("Read a file")]
    public async Task<string> ReadAsync([Description("Source file")] string path, CancellationToken cancellationToken = default)
    {
        using var reader = File.OpenText(path);
        return await reader.ReadToEndAsync(
#if NET6_0_OR_GREATER
            cancellationToken
#endif
            ).ConfigureAwait(false);
    }

    /// <summary>
    /// Write a file
    /// </summary>
    /// <example>
    /// {{file.writeAsync}}
    /// </example>
    /// <param name="path">The destination file path</param>
    /// <param name="content">The file content to write</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns> An awaitable task </returns>
    [KernelFunction, Description("Write a file")]
    public async Task WriteAsync(
        [Description("Destination file")] string path,
        [Description("File content")] string content,
        CancellationToken cancellationToken = default)
    {
        byte[] text = Encoding.UTF8.GetBytes(content);
        if (File.Exists(path) && File.GetAttributes(path).HasFlag(FileAttributes.ReadOnly))
        {
            // Most environments will throw this with OpenWrite, but running inside docker on Linux will not.
            throw new UnauthorizedAccessException($"File is read-only: {path}");
        }

        using var writer = File.OpenWrite(path);
        await writer.WriteAsync(
#if NET6_0_OR_GREATER
            text
#else
            text, 0, text.Length
#endif
            , cancellationToken).ConfigureAwait(false);
    }
}
