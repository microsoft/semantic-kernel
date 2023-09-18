// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Interface for cloud drive connections (e.g. OneDrive).
/// </summary>
public interface ICloudDriveConnector
{
    /// <summary>
    /// Create a shareable link to a file.
    /// </summary>
    /// <param name="filePath">Path to the file.</param>
    /// <param name="type">Type of link to create.</param>
    /// <param name="scope">Scope of the link.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Shareable link.</returns>
    Task<string> CreateShareLinkAsync(string filePath, string type = "view", string scope = "anonymous", CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the content of a file.
    /// </summary>
    /// <param name="filePath">Path to the remote file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<Stream> GetFileContentStreamAsync(string filePath, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upload a small file (less than 4MB).
    /// </summary>
    /// <param name="filePath">Path of the local file to upload.</param>
    /// <param name="destinationPath">Remote path to store the file, which is relative to the root of the OneDrive folder and should begin with the '/' character.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task UploadSmallFileAsync(string filePath, string destinationPath, CancellationToken cancellationToken = default);
}
