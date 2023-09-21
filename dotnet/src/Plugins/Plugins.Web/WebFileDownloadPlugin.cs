// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Plugins.Web;

/// <summary>
/// Plugin to download web files.
/// </summary>
public sealed class WebFileDownloadPlugin
{
    /// <summary>
    /// Plugin parameter: where to save file.
    /// </summary>
    public const string FilePathParamName = "filePath";

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="WebFileDownloadPlugin"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public WebFileDownloadPlugin(ILoggerFactory? loggerFactory = null) :
        this(new HttpClient(NonDisposableHttpClientHandler.Instance, false), loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WebFileDownloadPlugin"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public WebFileDownloadPlugin(HttpClient httpClient, ILoggerFactory? loggerFactory = null)
    {
        this._httpClient = httpClient;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(WebFileDownloadPlugin)) : NullLogger.Instance;
    }

    /// <summary>
    /// Downloads a file to a local file path.
    /// </summary>
    /// <param name="url">URI of file to download</param>
    /// <param name="filePath">Path where to save file locally</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>Task.</returns>
    /// <exception cref="KeyNotFoundException">Thrown when the location where to download the file is not provided</exception>
    [SKFunction, Description("Downloads a file to local storage")]
    public async Task DownloadToFileAsync(
        [Description("URL of file to download")] Uri url,
        [Description("Path where to save file locally")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug($"{nameof(this.DownloadToFileAsync)} got called");

        this._logger.LogDebug("Sending GET request for {0}", url);

        using HttpRequestMessage request = new(HttpMethod.Get, url);

        using HttpResponseMessage response = await this._httpClient.SendWithSuccessCheckAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {0}", response.StatusCode);

        using Stream webStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
        using FileStream outputFileStream = new(Environment.ExpandEnvironmentVariables(filePath), FileMode.Create);

        await webStream.CopyToAsync(outputFileStream, 81920 /*same value used by default*/, cancellationToken).ConfigureAwait(false);
    }
}
