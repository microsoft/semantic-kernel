// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Reliability;
using Polly;
using Polly.Retry;

namespace Reliability;

/// <summary>
/// A factory for creating a retry handler.
/// </summary>
public class RetryThreeTimesWithRetryAfterBackoffFactory : IDelegatingHandlerFactory
{
    public DelegatingHandler Create(ILogger? log)
    {
        return new RetryThreeTimesWithRetryAfterBackoff(log);
    }
}

/// <summary>
/// An example of a retry mechanism that retries three times with backoff using the RetryAfter value.
/// </summary>
public class RetryThreeTimesWithRetryAfterBackoff : DelegatingHandler
{
    private readonly AsyncRetryPolicy<HttpResponseMessage> _policy;

    public RetryThreeTimesWithRetryAfterBackoff(ILogger? log)
    {
        this._policy = GetPolicy(log);
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        return await this._policy.ExecuteAsync(async () =>
        {
            var response = await base.SendAsync(request, cancellationToken);
            return response;
        });
    }

    private static AsyncRetryPolicy<HttpResponseMessage> GetPolicy(ILogger? log)
    {
        // Handle 429 and 401 errors
        // Typically 401 would not be something we retry but for demonstration
        // purposes we are doing so as it's easy to trigger when using an invalid key.
        return Policy
            .HandleResult<HttpResponseMessage>(response =>
                response.StatusCode is System.Net.HttpStatusCode.TooManyRequests or System.Net.HttpStatusCode.Unauthorized)
            .WaitAndRetryAsync(
                retryCount: 3,
                sleepDurationProvider: (_, r, _) =>
                {
                    var response = r.Result;
                    var retryAfter = response.Headers.RetryAfter?.Delta ?? response.Headers.RetryAfter?.Date - DateTimeOffset.Now;
                    return retryAfter ?? TimeSpan.FromSeconds(2);
                },
                (outcome, timespan, retryCount, _) =>
                {
                    log?.LogWarning(
                        "Error executing action [attempt {0} of 3], pausing {1}ms. Outcome: {2}",
                        retryCount,
                        timespan.TotalMilliseconds,
                        outcome.Result.StatusCode);
                    return Task.CompletedTask;
                });
    }
}
