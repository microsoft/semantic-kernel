// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace FileCompression;

/// <summary>
/// Interface for file compression / decompression.
/// </summary>
public interface IFileCompressor
{
    /// <summary>
    /// Compress a source file to a destination file.
    /// </summary>
    /// <param name="sourceFilePath">File to compress</param>
    /// <param name="destinationFilePath">Compressed file to create</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Task</returns>
    public Task CompressFileAsync(string sourceFilePath, string destinationFilePath, CancellationToken cancellationToken);

    /// <summary>
    /// Compress a source directory to a destination file.
    /// </summary>
    /// <param name="sourceDirectoryPath">Directory to compress</param>
    /// <param name="destinationFilePath">Compressed file to create</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Task</returns>
    public Task CompressDirectoryAsync(string sourceDirectoryPath, string destinationFilePath, CancellationToken cancellationToken);

    /// <summary>
    /// Decompress a source file to a destination folder.
    /// </summary>
    /// <param name="sourceFilePath">File to decompress</param>
    /// <param name="destinationDirectoryPath">Directory into which to extract the decompressed content</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Task</returns>
    public Task DecompressFileAsync(string sourceFilePath, string destinationDirectoryPath, CancellationToken cancellationToken);
}
