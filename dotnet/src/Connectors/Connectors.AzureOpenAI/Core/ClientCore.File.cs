// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Files;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with Azure OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Uploads a file to Azure OpenAI.
    /// </summary>
    /// <param name="fileName">File name</param>
    /// <param name="fileContent">File content</param>
    /// <param name="purpose">Purpose of the file</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Uploaded file information</returns>
    internal async Task<OpenAIFileInfo> UploadFileAsync(
        string fileName,
        Stream fileContent,
        FileUploadPurpose purpose,
        CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfo> response = await RunRequestAsync(() => this.Client.GetFileClient().UploadFileAsync(fileContent, fileName, purpose, cancellationToken)).ConfigureAwait(false);
        return response.Value;
    }

    /// <summary>
    /// Delete a previously uploaded file.
    /// </summary>
    /// <param name="fileId">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    internal async Task DeleteFileAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        await RunRequestAsync(() => this.Client.GetFileClient().DeleteFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieve metadata for a previously uploaded file.
    /// </summary>
    /// <param name="fileId">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata associated with the specified file identifier.</returns>
    internal async Task<OpenAIFileInfo> GetFileAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfo> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
        return response.Value;
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    internal async Task<IEnumerable<OpenAIFileInfo>> GetFilesAsync(CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfoCollection> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFilesAsync(cancellationToken: cancellationToken)).ConfigureAwait(false);
        return response.Value;
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="filePurpose">The purpose of the files by which to filter.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    internal async Task<IEnumerable<OpenAIFileInfo>> GetFilesAsync(OpenAIFilePurpose? filePurpose, CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfoCollection> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFilesAsync(filePurpose, cancellationToken: cancellationToken)).ConfigureAwait(false);
        return response.Value;
    }

    /// <summary>
    /// Retrieve the file content from a previously uploaded file.
    /// </summary>
    /// <param name="fileId">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file content as <see cref="BinaryContent"/></returns>
    /// <remarks>
    /// Files uploaded with <see cref="OpenAIFilePurpose.Assistants"/> do not support content retrieval.
    /// </remarks>
    internal async Task<byte[]> GetFileContentAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        ClientResult<BinaryData> response = await RunRequestAsync(() => this.Client.GetFileClient().DownloadFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
        return response.Value.ToArray();
    }
}
