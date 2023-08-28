// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.Extensions.Logging;

internal static class HttpClientExtensions
{
    /// <summary>
    /// Sends an HTTP request using the provided <see cref="HttpClient"/> instance and checks for a successful response.
    /// If the response is not successful, it logs an error and throws an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="client">The <see cref="HttpClient"/> instance to use for sending the request.</param>
    /// <param name="request">The <see cref="HttpRequestMessage"/> to send.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/> for canceling the request.</param>
    /// <param name="logger">An optional <see cref="ILogger"/> instance for logging errors. (Default is null)</param>
    /// <returns>The <see cref="HttpResponseMessage"/> representing the response.</returns>
    public static async Task<HttpResponseMessage> SendAndCheckSuccessAsync(this HttpClient client, HttpRequestMessage request, CancellationToken cancellationToken, ILogger? logger = null)
    {
        HttpResponseMessage? response = null;

        try
        {
            response = await client.SendAsync(request, cancellationToken).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            return response;
        }
        catch (HttpRequestException e)
        {
            var responseContent = await response!.Content.ReadAsStringAsync().ConfigureAwait(false);

            logger?.LogError(e, "HTTP request failed: {StatusCode} {Message} {Content}", response!.StatusCode, e.Message, responseContent);

            throw new HttpOperationException(response!.StatusCode, responseContent, e.Message, e);
        }
    }
}
