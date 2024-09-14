// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AssemblyAI.Core;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// Service to upload files to AssemblyAI
/// </summary>
public sealed class AssemblyAIFileService
{
    private readonly AssemblyAIClient _client;

    /// <summary>
    /// Creates an instance of the <see cref="AssemblyAIFileService"/> with an AssemblyAI API key.
    /// </summary>
    /// <param name="apiKey">AssemblyAI API key</param>
    /// <param name="endpoint">Optional endpoint uri including the port where AssemblyAI server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the AssemblyAI API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public AssemblyAIFileService(
        string apiKey,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        public AssemblyAIFileService(string apiKey, Uri? endpoint = null, HttpClient? httpClient = null) : this(apiKey, endpoint, httpClient, null)
    )
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._client = new AssemblyAIClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            endpoint: endpoint,
            apiKey: apiKey,
            logger: loggerFactory?.CreateLogger(this.GetType()));
    }

    /// <summary>
    /// Upload a file.
    /// </summary>
    /// <param name="stream">The file stream</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file metadata.</returns>
    public async Task<AudioContent> UploadAsync(Stream stream, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(stream);
        var file = await this._client.UploadFileAsync(stream, cancellationToken).ConfigureAwait(false);
        return new AudioContent(new Uri(file, UriKind.Absolute));
    }
}
