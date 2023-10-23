// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.Client;

/// <summary>
/// An HTTPClient logging handler for ensuring diagnostic headers for Graph API calls are available.
/// </summary>
/// <remarks>
/// See https://github.com/microsoftgraph/msgraph-sdk-dotnet-core/blob/dev/docs/logging-requests.md
/// </remarks>
public class MsGraphClientLoggingHandler : DelegatingHandler
{
    /// <summary>
    /// From https://learn.microsoft.com/graph/best-practices-concept#reliability-and-support
    /// </summary>
    private const string ClientRequestIdHeaderName = "client-request-id";

    private readonly List<string> _headerNamesToLog = new()
    {
        ClientRequestIdHeaderName,
        "request-id",
        "x-ms-ags-diagnostic",
        "Date"
    };

    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="MsGraphClientLoggingHandler"/> class.
    /// </summary>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging.</param>
    public MsGraphClientLoggingHandler(ILogger logger)
    {
        this._logger = logger;
    }

    /// <summary>
    /// Sends an HTTP request to the inner handler to send to the server as an asynchronous operation.
    /// </summary>
    /// <param name="request">The request message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The task object representing the asynchronous operation.</returns>
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        request.Headers.Add(ClientRequestIdHeaderName, Guid.NewGuid().ToString());
        this.LogHttpMessage(request.Headers, request.RequestUri, "REQUEST");
        HttpResponseMessage response = await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
        this.LogHttpMessage(response.Headers, response.RequestMessage.RequestUri, "RESPONSE");
        return response;
    }

    /// <summary>
    /// Log the headers and URI of an HTTP message.
    /// </summary>
    private void LogHttpMessage(HttpHeaders headers, Uri uri, string prefix)
    {
        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            StringBuilder message = new();
            message.AppendLine($"{prefix} {uri}");
            foreach (string headerName in this._headerNamesToLog)
            {
                if (headers.TryGetValues(headerName, out IEnumerable<string> values))
                {
                    message.AppendLine($"{headerName}: {string.Join(", ", values)}");
                }
            }

            this._logger.LogDebug("{0}", message);
        }
    }
}
