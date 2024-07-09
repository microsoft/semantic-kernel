// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// File service access for Azure OpenAI.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIFileService
{
    /// <summary>
    /// Azure OpenAI client for HTTP operations.
    /// </summary>
    private readonly ClientCore _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIFileService"/> class.
    /// </summary>
    /// <param name="endpoint">Non-default endpoint for the OpenAI API.</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIFileService(
        Uri endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(apiKey, nameof(apiKey));

        this._client = new(endpoint.AbsoluteUri, apiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIFileService)));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIFileService"/> class.
    /// </summary>
    /// <param name="azureOpenAIClient">Custom <see cref="AzureOpenAIClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIFileService(
        AzureOpenAIClient azureOpenAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(azureOpenAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIFileService)));
    }

    /// <summary>
    /// Remove a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task DeleteFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));

        return this._client.DeleteFileAsync(id, cancellationToken);
    }

    /// <summary>
    /// Retrieve the file content from a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file content as <see cref="BinaryContent"/></returns>
    /// <remarks>
    /// Files uploaded with <see cref="AzureOpenAIFilePurpose.Assistants"/> do not support content retrieval.
    /// </remarks>
    public async Task<BinaryContent> GetFileContentAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));
        var bytes = await this._client.GetFileContentAsync(id, cancellationToken).ConfigureAwait(false);

        // The mime type of the downloaded file is not provided by the OpenAI API.
        return new(bytes, null);
    }

    /// <summary>
    /// Retrieve metadata for a previously uploaded file.
    /// </summary>
    /// <param name="id">The uploaded file identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata associated with the specified file identifier.</returns>
    public Task<AzureOpenAIFileReference> GetFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));
        return this._client.GetFileAsync(id, cancellationToken);
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    public async Task<IEnumerable<AzureOpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default)
        => await this._client.GetFilesAsync(cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Retrieve metadata for previously uploaded files
    /// </summary>
    /// <param name="filePurpose">The purpose of the files by which to filter.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    public async Task<IEnumerable<AzureOpenAIFileReference>> GetFilesAsync(AzureOpenAIFilePurpose? filePurpose, CancellationToken cancellationToken = default)
        => await this._client.GetFilesAsync(filePurpose, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Upload a file.
    /// </summary>
    /// <param name="fileContent">The file content as <see cref="BinaryContent"/></param>
    /// <param name="settings">The upload settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file metadata.</returns>
    public async Task<AzureOpenAIFileReference> UploadContentAsync(BinaryContent fileContent, AzureOpenAIFileUploadExecutionSettings settings, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(settings, nameof(settings));
        Verify.NotNull(fileContent.Data, nameof(fileContent.Data));

        using var memoryStream = new MemoryStream(fileContent.Data.Value.ToArray());
        return await this._client.UploadFileAsync(settings.FileName, memoryStream, settings.Purpose, cancellationToken).ConfigureAwait(false);
    }
}
