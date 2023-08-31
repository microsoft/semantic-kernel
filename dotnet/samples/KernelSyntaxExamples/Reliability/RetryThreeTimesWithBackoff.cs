// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Config;
using Polly;
using Polly.Retry;

namespace Reliability;

/// <summary>
/// A factory for creating a retry handler.
/// </summary>
public class RetryThreeTimesWithBackoffFactory : IDelegatingHandlerFactory
{
    public DelegatingHandler Create(ILoggerFactory? loggerFactory)
    {
        return new RetryThreeTimesWithBackoff(loggerFactory);
    }
}

/// <summary>
/// A basic example of a retry mechanism that retries three times with backoff.
/// </summary>
public class RetryThreeTimesWithBackoff : DelegatingHandler
{
    private readonly AsyncRetryPolicy<HttpResponseMessage> _policy;

    public RetryThreeTimesWithBackoff(ILoggerFactory? loggerFactory)
    {
        this._policy = GetPolicy(loggerFactory);
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        return await this._policy.ExecuteAsync(async () =>
        {
            var response = await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
            return response;
        }).ConfigureAwait(false);
    }

    private static AsyncRetryPolicy<HttpResponseMessage> GetPolicy(ILoggerFactory? logger)
    {
        // Handle 429 and 401 errors
        // Typically 401 would not be something we retry but for demonstration
        // purposes we are doing so as it's easy to trigger when using an invalid key.
        const int tooManyRequests = 429;
        const int unauthorized = 401;

        return Policy
            .HandleResult<HttpResponseMessage>(response =>
                (int)response.StatusCode is tooManyRequests or unauthorized)
            .WaitAndRetryAsync(new[]
                {
                    TimeSpan.FromSeconds(2),
                    TimeSpan.FromSeconds(4),
                    TimeSpan.FromSeconds(8)
                },
                (outcome, timespan, retryCount, _) => logger?.CreateLogger(nameof(RetryThreeTimesWithBackoff)).LogWarning(
                    "Error executing action [attempt {0} of 3], pausing {1}ms. Outcome: {2}",
                    retryCount,
                    timespan.TotalMilliseconds,
                    outcome.Result.StatusCode));
    }
}
