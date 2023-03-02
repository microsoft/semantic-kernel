// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.OpenAI.Clients;

internal class RetryHandler: DelegatingHandler
{
    private const string Retry_After = "Retry-After";
    private const int MaxRetries = 10;

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        int retryCount = 0;

        while (true)
        {
            // Throw an exception if we've requested to cancel the operation
            cancellationToken.ThrowIfCancellationRequested();

            // Issue the request
            HttpResponseMessage response = await base.SendAsync(request, cancellationToken);

            // If the request does not require a retry then we're done
            if (!ShouldRetry(response.StatusCode))
            {
                return response;
            }

            // Drain response content to free connections. Need to perform this
            // before retry attempt and before the TooManyRetries ServiceException.
            if (response.Content != null)
            {                
#if NET5_0_OR_GREATER
                await response.Content.ReadAsByteArrayAsync(cancellationToken).ConfigureAwait(false);
#else
                await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
#endif
            }

            // Safety measure to not keep retrying forever
            if (retryCount >= MaxRetries)
            {
                throw new AIException(AIException.ErrorCodes.UnknownError,
                    $"Request reached it's max retry count of {retryCount}");
            }

            // Prepare Delay task configured with the delay time from response's Retry-After header
            var waitTime = CalculateWaitTime(response);
            Task delay = Task.Delay(waitTime, cancellationToken);

            // Clone request with CloneAsync before retrying
            // Do not dispose this request as that breaks the request cloning
#pragma warning disable CA2000
            request = await CloneAsync(request);
#pragma warning restore CA2000

            // Increase retryCount
            retryCount++;

            // Delay time based upon Retry-After header
            await delay;
        }
    }

    private static TimeSpan CalculateWaitTime(HttpResponseMessage response)
    {
        // Default delay, in case the retry-after header data is corrupt
        double delayInSeconds = 10;

        if (response != null && response.Headers.TryGetValues(Retry_After, out IEnumerable<string> values))
        {
            // Can we use the provided retry-after header?
            string retryAfter = values.First();
            if (int.TryParse(retryAfter, out int delaySeconds))
            {
                delayInSeconds = delaySeconds;
            }
        }

        return TimeSpan.FromSeconds(delayInSeconds);
    }

    internal static bool ShouldRetry(HttpStatusCode statusCode)
    {
        return (statusCode == HttpStatusCode.ServiceUnavailable ||
                statusCode == HttpStatusCode.GatewayTimeout ||
                statusCode == (HttpStatusCode)429);
    }

    /// <summary>
    /// Create a new HTTP request by copying previous HTTP request's headers and properties from response's request message.
    /// Copied from: https://github.com/microsoftgraph/msgraph-sdk-dotnet-core/blob/dev/src/Microsoft.Graph.Core/Extensions/HttpRequestMessageExtensions.cs
    /// </summary>
    /// <param name="originalRequest">The previous <see cref="HttpRequestMessage"/> needs to be copy.</param>
    /// <returns>The <see cref="HttpRequestMessage"/>.</returns>
    /// <remarks>
    /// Re-issue a new HTTP request with the previous request's headers and properities
    /// </remarks>
    internal static async Task<HttpRequestMessage> CloneAsync(HttpRequestMessage originalRequest)
    {
        var newRequest = new HttpRequestMessage(originalRequest.Method, originalRequest.RequestUri);

        // Copy request headers.
        foreach (var header in originalRequest.Headers)
        {
            newRequest.Headers.TryAddWithoutValidation(header.Key, header.Value);
        }

        // Copy request properties.
#if NET5_0_OR_GREATER
#pragma warning disable CS0618 // Type or member is obsolete
#endif
        foreach (var property in originalRequest.Properties)
        {
            newRequest.Properties.Add(property);
        }
#if NET5_0_OR_GREATER
#pragma warning restore CS0618 // Type or member is obsolete
#endif

        // Set Content if previous request had one.
        if (originalRequest.Content != null)
        {
            // HttpClient doesn't rewind streams and we have to explicitly do so.
            await originalRequest.Content.ReadAsStreamAsync().ContinueWith(t =>
            {
                if (t.Result.CanSeek)
                {
                    t.Result.Seek(0, SeekOrigin.Begin);
                }

                newRequest.Content = new StreamContent(t.Result);
            }).ConfigureAwait(false);

            // Copy content headers.
            if (originalRequest.Content.Headers != null)
            {
                foreach (var contentHeader in originalRequest.Content.Headers)
                {
                    newRequest.Content.Headers.TryAddWithoutValidation(contentHeader.Key, contentHeader.Value);
                }
            }
        }

        return newRequest;
    }

}
