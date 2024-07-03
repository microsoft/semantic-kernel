// Copyright (c) Microsoft. All rights reserved.

/* 
Phase 05

- Ignoring the specific Purposes not implemented by current FileService.
*/

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Files;

using OAIFilePurpose = OpenAI.Files.OpenAIFilePurpose;
using SKFilePurpose = Microsoft.SemanticKernel.Connectors.OpenAI.OpenAIFilePurpose;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    internal async Task<OpenAIFileReference> UploadFileAsync(
        string fileName,
        Stream fileContent,
        SKFilePurpose purpose,
        CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfo> response = await RunRequestAsync(() => this.Client.GetFileClient().UploadFileAsync(fileContent, fileName, ConvertToOpenAIFilePurpose(purpose), cancellationToken)).ConfigureAwait(false);
        return ConvertToFileReference(response.Value);
    }

    internal async Task DeleteFileAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        await RunRequestAsync(() => this.Client.GetFileClient().DeleteFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
    }

    internal async Task<OpenAIFileReference> GetFileAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfo> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
        return ConvertToFileReference(response.Value);
    }

    internal async Task<IList<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfoCollection> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFilesAsync(cancellationToken: cancellationToken)).ConfigureAwait(false);
        return response.Value
            .Select(ConvertToFileReference)
            .ToList();
    }

    internal async Task<byte[]> GetFileContentAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        ClientResult<BinaryData> response = await RunRequestAsync(() => this.Client.GetFileClient().DownloadFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
        return response.Value.ToArray();
    }

    private static OpenAIFileReference ConvertToFileReference(OpenAIFileInfo fileInfo)
        => new()
        {
            Id = fileInfo.Id,
            CreatedTimestamp = fileInfo.CreatedAt.DateTime,
            FileName = fileInfo.Filename,
            SizeInBytes = (int)(fileInfo.SizeInBytes ?? 0),
            Purpose = ConvertToFilePurpose(fileInfo.Purpose),
        };

    private static FileUploadPurpose ConvertToOpenAIFilePurpose(SKFilePurpose purpose)
    {
        if (SKFilePurpose.FineTune == purpose) { return FileUploadPurpose.FineTune; }
        if (SKFilePurpose.Assistants == purpose) { return FileUploadPurpose.Assistants; }

        /* WIB - Ignoring the following cases for now
        if (SKFilePurpose.Vision == purpose) { return FileUploadPurpose.Vision; }
        if (SKFilePurpose.Batch == purpose) { return FileUploadPurpose.Batch; }
        */

        throw new NotSupportedException($"Unsupported file purpose: {purpose}");
    }

    private static SKFilePurpose ConvertToFilePurpose(OAIFilePurpose purpose)
    {
        if (OAIFilePurpose.FineTune == purpose) { return SKFilePurpose.FineTune; }
        if (OAIFilePurpose.Assistants == purpose) { return SKFilePurpose.Assistants; }

        /* WIB - Ignoring the following cases for now
        if (OAIFilePurpose.FineTuneResults == purpose) { return SKFilePurpose.FineTuneResults; }
        if (OAIFilePurpose.AssistantsOutput == purpose) { return SKFilePurpose.AssistantsOutput; }
        if (OAIFilePurpose.Vision == purpose) { return SKFilePurpose.Vision; }
        if (OAIFilePurpose.Batch == purpose) { return SKFilePurpose.Batch; }
        if (OAIFilePurpose.BatchOutput == purpose) { return SKFilePurpose.BatchOutput; }
        if (OAIFilePurpose.FineTuneResults == purpose) { return SKFilePurpose.FineTuneResults; }
        */

        throw new NotSupportedException($"Unsupported file purpose: {purpose}");
    }
}
