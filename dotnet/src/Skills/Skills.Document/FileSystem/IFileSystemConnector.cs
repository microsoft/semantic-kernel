// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.Document.FileSystem;

/// <summary>
/// Interface for filesystem connections.
/// </summary>
public interface IFileSystemConnector
{
    /// <summary>
    /// Get the contents of a file as a read-only stream.
    /// </summary>
    /// <param name="filePath">Path to the file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task<Stream> GetFileContentStreamAsync(string filePath, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get a writeable stream to an existing file.
    /// </summary>
    /// <param name="filePath">Path to file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task<Stream> GetWriteableFileStreamAsync(string filePath, CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a new file and get a writeable stream to it.
    /// </summary>
    /// <param name="filePath">Path to file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task<Stream> CreateFileAsync(string filePath, CancellationToken cancellationToken = default);

    /// <summary>
    /// Determine whether a file exists at the specified path.
    /// </summary>
    /// <param name="filePath">Path to file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True if file exists, false otherwise.</returns>
    public Task<bool> FileExistsAsync(string filePath, CancellationToken cancellationToken = default);
}
