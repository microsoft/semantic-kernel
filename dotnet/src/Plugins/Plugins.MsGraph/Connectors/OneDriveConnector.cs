// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.Diagnostics;
namespace Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;

/// <summary>
/// Connector for OneDrive API
/// </summary>
public class OneDriveConnector : ICloudDriveConnector
{
    private readonly GraphServiceClient _graphServiceClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="OneDriveConnector"/> class.
    /// </summary>
    /// <param name="graphServiceClient">A graph service client.</param>
    public OneDriveConnector(GraphServiceClient graphServiceClient)
    {
        this._graphServiceClient = graphServiceClient;
    }

    /// <inheritdoc/>
    public async Task<Stream> GetFileContentStreamAsync(string filePath, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));

        return await this._graphServiceClient.Me
            .Drive.Root
            .ItemWithPath(filePath).Content
            .Request().GetAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Checks if a file exists at the specified path in OneDrive.
    /// </summary>
    /// <param name="filePath">The path to the file in OneDrive.</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>A <see cref="Task{TResult}"/> representing the result of the asynchronous operation. True if the file exists, false otherwise.</returns>
    public async Task<bool> FileExistsAsync(string filePath, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));

        try
        {
            await this._graphServiceClient.Me
                .Drive.Root
                .ItemWithPath(filePath).Request().GetAsync(cancellationToken).ConfigureAwait(false);

            // If no exception is thrown, the file exists.
            return true;
        }
        catch (ServiceException ex)
        {
            // If the exception is a 404 Not Found, the file does not exist.
            if (ex.StatusCode == HttpStatusCode.NotFound)
            {
                return false;
            }

            throw new HttpOperationException(ex.StatusCode, responseContent: null, ex.Message, ex);
        }
    }

    /// <inheritdoc/>
    public async Task UploadSmallFileAsync(string filePath, string destinationPath, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));
        Ensure.NotNullOrWhitespace(destinationPath, nameof(destinationPath));

        filePath = Environment.ExpandEnvironmentVariables(filePath);

        long fileSize = new FileInfo(filePath).Length;
        if (fileSize > 4 * 1024 * 1024)
        {
            throw new IOException("File is too large to upload - function currently only supports files up to 4MB.");
        }

        using FileStream fileContentStream = new(filePath, FileMode.Open, FileAccess.Read);

        GraphResponse<DriveItem>? response = null;

        try
        {
            response = await this._graphServiceClient.Me
                .Drive.Root
                .ItemWithPath(destinationPath).Content
                .Request().PutResponseAsync<DriveItem>(fileContentStream, cancellationToken, HttpCompletionOption.ResponseContentRead).ConfigureAwait(false);

            response.ToHttpResponseMessage().EnsureSuccessStatusCode();
        }
        catch (ServiceException ex)
        {
            throw new HttpOperationException(ex.StatusCode, responseContent: null, ex.Message, ex);
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(response?.StatusCode, responseContent: null, ex.Message, ex);
        }
    }

    /// <inheritdoc/>
    public async Task<string> CreateShareLinkAsync(string filePath, string type = "view", string scope = "anonymous",
        CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(filePath, nameof(filePath));
        Ensure.NotNullOrWhitespace(type, nameof(type));
        Ensure.NotNullOrWhitespace(scope, nameof(scope));

        GraphResponse<Permission>? response = null;

        try
        {
            response = await this._graphServiceClient.Me
               .Drive.Root
               .ItemWithPath(filePath)
               .CreateLink(type, scope)
               .Request().PostResponseAsync(cancellationToken).ConfigureAwait(false);

            response.ToHttpResponseMessage().EnsureSuccessStatusCode();
        }
        catch (ServiceException ex)
        {
            throw new HttpOperationException(ex.StatusCode, responseContent: null, ex.Message, ex);
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(response?.StatusCode, responseContent: null, ex.Message, ex);
        }

        string? result = (await response.GetResponseObjectAsync().ConfigureAwait(false)).Link?.WebUrl;
        if (string.IsNullOrWhiteSpace(result))
        {
            throw new SKException("Shareable file link was null or whitespace.");
        }

        return result!;
    }
}
