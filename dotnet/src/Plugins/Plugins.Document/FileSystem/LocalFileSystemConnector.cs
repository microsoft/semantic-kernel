// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Document.FileSystem;

#pragma warning disable CA1031 // Exceptions are caught and returned in a task

/// <summary>
/// Connector for local filesystem
/// </summary>
public class LocalFileSystemConnector : IFileSystemConnector
{
    /// <summary>
    /// Get the contents of a file as a read-only stream.
    /// </summary>
    /// <param name="filePath">Path to file</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <exception cref="ArgumentException"></exception>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="PathTooLongException"></exception>
    /// <exception cref="DirectoryNotFoundException"></exception>
    /// <exception cref="IOException"></exception>
    /// <exception cref="UnauthorizedAccessException"></exception>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    /// <exception cref="FileNotFoundException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    public Task<Stream> GetFileContentStreamAsync(string filePath, CancellationToken cancellationToken = default)
    {
        try
        {
            return Task.FromResult<Stream>(File.Open(Environment.ExpandEnvironmentVariables(filePath), FileMode.Open, FileAccess.Read));
        }
        catch (Exception e)
        {
            return Task.FromException<Stream>(e);
        }
    }

    /// <summary>
    /// Get a writeable stream to a file.
    /// </summary>
    /// <param name="filePath">Path to file</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <exception cref="ArgumentException"></exception>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="PathTooLongException"></exception>
    /// <exception cref="DirectoryNotFoundException"></exception>
    /// <exception cref="IOException"></exception>
    /// <exception cref="UnauthorizedAccessException"></exception>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    /// <exception cref="FileNotFoundException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    public Task<Stream> GetWriteableFileStreamAsync(string filePath, CancellationToken cancellationToken = default)
    {
        try
        {
            return Task.FromResult<Stream>(File.Open(Environment.ExpandEnvironmentVariables(filePath), FileMode.Open, FileAccess.ReadWrite));
        }
        catch (Exception e)
        {
            return Task.FromException<Stream>(e);
        }
    }

    /// <summary>
    /// Get a writeable stream to a file.
    /// </summary>
    /// <param name="filePath">Path to file</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <exception cref="ArgumentException"></exception>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="PathTooLongException"></exception>
    /// <exception cref="DirectoryNotFoundException"></exception>
    /// <exception cref="IOException"></exception>
    /// <exception cref="UnauthorizedAccessException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    public Task<Stream> CreateFileAsync(string filePath, CancellationToken cancellationToken = default)
    {
        try
        {
            return Task.FromResult<Stream>(File.Create(Environment.ExpandEnvironmentVariables(filePath)));
        }
        catch (Exception e)
        {
            return Task.FromException<Stream>(e);
        }
    }

    /// <inheritdoc/>
    public Task<bool> FileExistsAsync(string filePath, CancellationToken cancellationToken = default)
    {
        try
        {
            return Task.FromResult(File.Exists(Environment.ExpandEnvironmentVariables(filePath)));
        }
        catch (Exception e)
        {
            return Task.FromException<bool>(e);
        }
    }
}
