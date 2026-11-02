// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Document.FileSystem;

#pragma warning disable CA1031 // Exceptions are returned in the task, matching the connector contract.

/// <summary>
/// Connector for local filesystem access restricted to trusted directories.
/// </summary>
public class LocalFileSystemConnector : IFileSystemConnector
{
    /// <inheritdoc/>
    public Task<Stream> GetFileContentStreamAsync(
        string filePath, IEnumerable<string> allowedDirectories, CancellationToken cancellationToken = default)
    {
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            return Task.FromResult<Stream>(SecureFileSystem.OpenRead(
                filePath, allowedDirectories, out _, share: FileShare.None));
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            return Task.FromCanceled<Stream>(cancellationToken);
        }
        catch (Exception ex)
        {
            return Task.FromException<Stream>(ex);
        }
    }

    /// <inheritdoc/>
    public Task<(Stream Stream, bool Created)> OpenUpdateAsync(
        string filePath, IEnumerable<string> allowedDirectories, CancellationToken cancellationToken = default)
    {
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            Stream stream = SecureFileSystem.OpenUpdate(filePath, allowedDirectories, out var created);
            return Task.FromResult((stream, created));
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            return Task.FromCanceled<(Stream, bool)>(cancellationToken);
        }
        catch (Exception ex)
        {
            return Task.FromException<(Stream, bool)>(ex);
        }
    }
}
