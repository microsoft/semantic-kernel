// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Document.FileSystem;

/// <summary>
/// Interface for filesystem connections.
/// </summary>
public interface IFileSystemConnector
{
    /// <summary>
    /// Get the contents of a file as a read-only stream.
    /// </summary>
    /// <param name="filePath">Path to the file.</param>
    /// <param name="allowedDirectories">Nonempty list of trusted directories. The connector must
    /// enforce this restriction while opening the file, not just check a path before opening it.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<Stream> GetFileContentStreamAsync(
        string filePath, IEnumerable<string> allowedDirectories, CancellationToken cancellationToken = default);

    /// <summary>
    /// Securely open or create a document without truncating existing content.
    /// </summary>
    /// <param name="filePath">Path to file.</param>
    /// <param name="allowedDirectories">Nonempty list of trusted directories. Opening must not
    /// follow a replacement link outside these directories.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A caller-owned, seekable read/write stream and whether this operation created
    /// the file. Creation must be determined by the open itself, not a separate existence check.</returns>
    Task<(Stream Stream, bool Created)> OpenUpdateAsync(
        string filePath, IEnumerable<string> allowedDirectories, CancellationToken cancellationToken = default);
}
