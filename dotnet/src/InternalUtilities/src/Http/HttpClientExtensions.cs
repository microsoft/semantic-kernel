// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

internal static class HttpClientExtensions
{
    /// <summary>
    /// Sends an HTTP request using the provided <see cref="HttpClient"/> instance and checks for a successful response.
    /// If the response is not successful, it logs an error and throws an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="client">The <see cref="HttpClient"/> instance to use for sending the request.</param>
    /// <param name="request">The <see cref="HttpRequestMessage"/> to send.</param>
    /// <param name="completionOption">Indicates if HttpClient operations should be considered completed either as soon as a response is available,
    /// or after reading the entire response message including the content.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/> for canceling the request.</param>
    /// <returns>The <see cref="HttpResponseMessage"/> representing the response.</returns>
    [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1031:Do not catch general exception types", Justification = "By design. See comment below.")]
    internal static async Task<HttpResponseMessage> SendWithSuccessCheckAsync(this HttpClient client, HttpRequestMessage request, HttpCompletionOption completionOption, CancellationToken cancellationToken)
    {
        HttpResponseMessage? response = null;

        try
        {
            response = await client.SendAsync(request, completionOption, cancellationToken).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            return response;
        }
        catch (HttpRequestException e)
        {
            string? responseContent = null;

            try
            {
                responseContent = await response!.Content.ReadAsStringAsync().ConfigureAwait(false);
            }
            catch { } // We want to suppress any exceptions that occur while reading the content, ensuring that an HttpOperationException is thrown instead.

            throw new HttpOperationException(response!.StatusCode, responseContent, e.Message, e);
        }
    }

    /// <summary>
    /// Sends an HTTP request using the provided <see cref="HttpClient"/> instance and checks for a successful response.
    /// If the response is not successful, it logs an error and throws an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="client">The <see cref="HttpClient"/> instance to use for sending the request.</param>
    /// <param name="request">The <see cref="HttpRequestMessage"/> to send.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/> for canceling the request.</param>
    /// <returns>The <see cref="HttpResponseMessage"/> representing the response.</returns>
    internal static async Task<HttpResponseMessage> SendWithSuccessCheckAsync(this HttpClient client, HttpRequestMessage request, CancellationToken cancellationToken)
    {
        return await client.SendWithSuccessCheckAsync(request, HttpCompletionOption.ResponseContentRead, cancellationToken).ConfigureAwait(false);
    }
}
