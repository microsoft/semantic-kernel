// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// File service access for OpenAI: https://api.openai.com/v1/files
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAIFileService
{
    /// <summary>
    /// OpenAI client for HTTP operations.
    /// </summary>
    private readonly ClientCore _client;

    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="endpoint">Non-default endpoint for the OpenAI API.</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIFileService(
        Uri endpoint,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(apiKey, nameof(apiKey));

        this._client = new(null, apiKey, organization, endpoint, httpClient, loggerFactory?.CreateLogger(typeof(OpenAIFileService)));
    }

    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIFileService(
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(apiKey, nameof(apiKey));

        this._client = new(null, apiKey, organization, null, httpClient, loggerFactory?.CreateLogger(typeof(OpenAIFileService)));
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
    /// Files uploaded with <see cref="OpenAIFilePurpose.Assistants"/> do not support content retrieval.
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
    public Task<OpenAIFileReference> GetFileAsync(string id, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(id, nameof(id));
        return this._client.GetFileAsync(id, cancellationToken);
    }

    /// <summary>
    /// Retrieve metadata for all previously uploaded files.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The metadata of all uploaded files.</returns>
    public async Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default)
        => await this._client.GetFilesAsync(cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Upload a file.
    /// </summary>
    /// <param name="fileContent">The file content as <see cref="BinaryContent"/></param>
    /// <param name="settings">The upload settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file metadata.</returns>
    public async Task<OpenAIFileReference> UploadContentAsync(BinaryContent fileContent, OpenAIFileUploadExecutionSettings settings, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(settings, nameof(settings));
        Verify.NotNull(fileContent.Data, nameof(fileContent.Data));

        using var memoryStream = new MemoryStream(fileContent.Data.Value.ToArray());
        return await this._client.UploadFileAsync(settings.FileName, memoryStream, settings.Purpose, cancellationToken).ConfigureAwait(false);
    }
}
