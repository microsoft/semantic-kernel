// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Logging;
using OpenAI.Files;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with Azure OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ClientCore"/> class.
    /// </summary>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        Verify.NotNullOrWhiteSpace(apiKey);

        var options = GetAzureOpenAIClientOptions(httpClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.Endpoint = new Uri(endpoint);
        this.Client = new AzureOpenAIClient(this.Endpoint, apiKey, options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ClientCore"/> class.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="openAIClient">Custom <see cref="AzureOpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        AzureOpenAIClient openAIClient,
        ILogger? logger = null)
    {
        Verify.NotNull(openAIClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.Client = openAIClient;
    }

    /// <summary>
    /// Uploads a file to Azure OpenAI.
    /// </summary>
    /// <param name="fileName">File name</param>
    /// <param name="fileContent">File content</param>
    /// <param name="purpose">Purpose of the file</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Uploaded file information</returns>
    internal async Task<AzureOpenAIFileReference> UploadFileAsync(
        string fileName,
        Stream fileContent,
        AzureOpenAIFileUploadPurpose purpose,
        CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfo> response = await RunRequestAsync(() => this.Client.GetFileClient().UploadFileAsync(fileContent, fileName, ConvertToOpenAIFileUploadPurpose(purpose), cancellationToken)).ConfigureAwait(false);
        return ConvertToFileReference(response.Value);
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
    internal async Task<AzureOpenAIFileReference> GetFileAsync(
        string fileId,
        CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfo> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFileAsync(fileId, cancellationToken)).ConfigureAwait(false);
        return ConvertToFileReference(response.Value);
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    internal async Task<IEnumerable<AzureOpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken)
    {
        ClientResult<OpenAIFileInfoCollection> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFilesAsync(cancellationToken: cancellationToken)).ConfigureAwait(false);
        return response.Value.Select(ConvertToFileReference);
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="filePurpose">The purpose of the files by which to filter.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    internal async Task<IEnumerable<AzureOpenAIFileReference>> GetFilesAsync(AzureOpenAIFilePurpose? filePurpose, CancellationToken cancellationToken)
    {
        OpenAIFilePurpose? purpose = filePurpose.HasValue ? ConvertToOpenAIFilePurpose(filePurpose.Value) : null;
        ClientResult<OpenAIFileInfoCollection> response = await RunRequestAsync(() => this.Client.GetFileClient().GetFilesAsync(purpose, cancellationToken: cancellationToken)).ConfigureAwait(false);
        return response.Value.Select(ConvertToFileReference);
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

    private static AzureOpenAIFileReference ConvertToFileReference(OpenAIFileInfo fileInfo)
        => new()
        {
            Id = fileInfo.Id,
            CreatedTimestamp = fileInfo.CreatedAt.DateTime,
            FileName = fileInfo.Filename,
            SizeInBytes = (int)(fileInfo.SizeInBytes ?? 0),
            Purpose = ConvertToAzureOpenAIFilePurpose(fileInfo.Purpose),
        };

    private static FileUploadPurpose ConvertToOpenAIFileUploadPurpose(AzureOpenAIFileUploadPurpose purpose)
    {
        if (purpose == AzureOpenAIFileUploadPurpose.Assistants) { return FileUploadPurpose.Assistants; }
        if (purpose == AzureOpenAIFileUploadPurpose.FineTune) { return FileUploadPurpose.FineTune; }
        if (purpose == AzureOpenAIFileUploadPurpose.Vision) { return FileUploadPurpose.Vision; }
        if (purpose == AzureOpenAIFileUploadPurpose.Batch) { return FileUploadPurpose.Batch; }

        throw new KernelException($"Unknown {nameof(AzureOpenAIFileUploadPurpose)}: {purpose}.");
    }

    private static OpenAIFilePurpose ConvertToOpenAIFilePurpose(AzureOpenAIFilePurpose purpose)
    {
        if (purpose == AzureOpenAIFilePurpose.Assistants) { return OpenAIFilePurpose.Assistants; }
        if (purpose == AzureOpenAIFilePurpose.FineTune) { return OpenAIFilePurpose.FineTune; }
        if (purpose == AzureOpenAIFilePurpose.AssistantsOutput) { return OpenAIFilePurpose.AssistantsOutput; }
        if (purpose == AzureOpenAIFilePurpose.FineTuneResults) { return OpenAIFilePurpose.FineTuneResults; }
        if (purpose == AzureOpenAIFilePurpose.Vision) { return OpenAIFilePurpose.Vision; }
        if (purpose == AzureOpenAIFilePurpose.Batch) { return OpenAIFilePurpose.Batch; }
        if (purpose == AzureOpenAIFilePurpose.BatchOutput) { return OpenAIFilePurpose.BatchOutput; }

        throw new KernelException($"Unknown {nameof(AzureOpenAIFilePurpose)}: {purpose}.");
    }

    private static AzureOpenAIFilePurpose ConvertToAzureOpenAIFilePurpose(OpenAIFilePurpose purpose)
    {
        if (purpose == OpenAIFilePurpose.Assistants) { return AzureOpenAIFilePurpose.Assistants; }
        if (purpose == OpenAIFilePurpose.FineTune) { return AzureOpenAIFilePurpose.FineTune; }
        if (purpose == OpenAIFilePurpose.AssistantsOutput) { return AzureOpenAIFilePurpose.AssistantsOutput; }
        if (purpose == OpenAIFilePurpose.FineTuneResults) { return AzureOpenAIFilePurpose.FineTuneResults; }
        if (purpose == OpenAIFilePurpose.Vision) { return AzureOpenAIFilePurpose.Vision; }
        if (purpose == OpenAIFilePurpose.Batch) { return AzureOpenAIFilePurpose.Batch; }
        if (purpose == OpenAIFilePurpose.BatchOutput) { return AzureOpenAIFilePurpose.BatchOutput; }

        throw new KernelException($"Unknown {nameof(OpenAIFilePurpose)}: {purpose}.");
    }
}
