// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Polly;

namespace Microsoft.SemanticKernel.Reliability.Polly;

/// <summary>
/// Default retry handler implementation.
/// </summary>
internal class DefaultHttpRetryHandler : DelegatingHandler
{
    private readonly AsyncPolicy<HttpResponseMessage> _policy;
    private readonly ILogger<DefaultHttpRetryHandler>? _logger;
    private readonly HttpRetryConfig _config;
    private readonly ITimeProvider _timeProvider;

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with the provided configuration.
    /// </summary>
    /// <param name="config">Retry configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    internal DefaultHttpRetryHandler(HttpRetryConfig? config = null, ILoggerFactory? loggerFactory = null) : this(config, null, loggerFactory)
    {
    }

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with the provided configuration.
    /// </summary>
    /// <param name="config">Retry configuration</param>
    /// <param name="timeProvider">Time provider abstraction</param>
    /// <param name="loggerFactory">Logger factory</param>
    internal DefaultHttpRetryHandler(HttpRetryConfig? config, ITimeProvider? timeProvider, ILoggerFactory? loggerFactory)
    {
        this._logger = loggerFactory?.CreateLogger<DefaultHttpRetryHandler>();
        this._config = config ?? new();
        this._policy = this.GetPolicy();
        this._timeProvider = timeProvider ?? new DefaultTimeProvider();
    }

    /// <inheritdoc/>
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        return await this._policy.ExecuteAsync(async (cancelToken) =>
        {
            var response = await base.SendAsync(request, cancelToken).ConfigureAwait(false);
            return response;
        }, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates a policy based in the provided configuration.
    /// </summary>
    /// <returns>Returns the async policy executor</returns>
    private AsyncPolicy<HttpResponseMessage> GetPolicy()
    {
        if (this.IsRetryDisabled())
        {
            return Policy.NoOpAsync<HttpResponseMessage>();
        }

        var policyBuilder = Policy.HandleResult<HttpResponseMessage>(response =>
            {
                return this._config.RetryableStatusCodes.Contains(response.StatusCode);
            });

        policyBuilder = policyBuilder.Or<Exception>(e => this._config.RetryableExceptionTypes.Contains(e.GetType()));

        var timeoutPolicy = Policy.TimeoutAsync<HttpResponseMessage>(this._config.MaxTotalRetryTime);

        var retryPolicy = policyBuilder.WaitAndRetryAsync(
            retryCount: this._config.MaxRetryCount,
            sleepDurationProvider: (retryCount, context, timeSpan) =>
            {
                return this.GetWaitTime(retryCount, context.Result);
            },
            (outcome, timespan, retryCount, _) =>
            {
                this._logger?.LogWarning(
                    "Error executing action [attempt {CurrentRetryAttempt} of {MaxRetryAttempts}]. Reason: {StatusCode}. Will retry after {WaitMilliseconds}ms.",
                    retryCount,
                    this._config.MaxRetryCount,
                    outcome.Result.StatusCode,
                    timespan.TotalMilliseconds);
                return Task.CompletedTask;
            });

        return Policy.WrapAsync(timeoutPolicy, retryPolicy);
    }

    /// <summary>
    /// Checks if retry is disabled.
    /// </summary>
    /// <returns>Returns true when disabled</returns>
    private bool IsRetryDisabled()
    {
        return this._config.MaxRetryCount == 0;
    }

    /// <summary>
    /// Get the wait time for the next retry.
    /// </summary>
    /// <param name="retryCount">Current retry count</param>
    /// <param name="response">The response message that potentially contains RetryAfter header.</param>
    private TimeSpan GetWaitTime(int retryCount, HttpResponseMessage? response)
    {
        // If the response contains a RetryAfter header, use that value
        // Otherwise, use the configured min retry delay
        var retryAfter = response?.Headers.RetryAfter?.Date.HasValue == true
            ? response?.Headers.RetryAfter?.Date - this._timeProvider.GetCurrentTime()
            : (response?.Headers.RetryAfter?.Delta) ?? this._config.MinRetryDelay;
        retryAfter ??= this._config.MinRetryDelay;

        // If the retry delay is longer than the max retry delay, use the max retry delay
        var timeToWait = retryAfter > this._config.MaxRetryDelay
            ? this._config.MaxRetryDelay
            : retryAfter < this._config.MinRetryDelay
                ? this._config.MinRetryDelay
                : retryAfter ?? default;

        // If exponential backoff is enabled, and the server didn't provide a RetryAfter header, double the delay for each retry
        if (this._config.UseExponentialBackoff && response?.Headers.RetryAfter?.Date.HasValue == false)
        {
            for (var backoffRetryCount = 1; backoffRetryCount < retryCount + 1; backoffRetryCount++)
            {
                timeToWait = timeToWait.Add(timeToWait);
            }
        }

        return timeToWait;
    }

    /// <summary>
    /// Interface for a time provider, primarily to enable unit testing.
    /// </summary>
    internal interface ITimeProvider
    {
        DateTimeOffset GetCurrentTime();
    }

    /// <summary>
    /// Concrete implementation of <see cref="ITimeProvider"/> that returns the current time.
    /// </summary>
    internal sealed class DefaultTimeProvider : ITimeProvider
    {
        public DateTimeOffset GetCurrentTime()
        {
            return DateTimeOffset.UtcNow;
        }
    }
}
