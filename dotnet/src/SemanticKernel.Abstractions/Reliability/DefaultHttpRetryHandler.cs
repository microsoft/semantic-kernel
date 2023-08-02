// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Reliability;

[Obsolete("Internal Semantic Kernel Retry logic is being deprecated")]
public sealed class DefaultHttpRetryHandler : DelegatingHandler
{
    /// <summary>
    /// Initializes a new instance of the <see cref="DefaultHttpRetryHandler"/> class.
    /// </summary>
    /// <param name="config">The retry configuration.</param>
    /// <param name="logger">The logger.</param>
    public DefaultHttpRetryHandler(HttpRetryConfig? config = null, ILogger? logger = null)
        : this(config ?? new HttpRetryConfig(), logger, null, null)
    {
    }

    internal DefaultHttpRetryHandler(
        HttpRetryConfig config,
        ILogger? logger = null,
        IDelayProvider? delayProvider = null,
        ITimeProvider? timeProvider = null)
    {
        this._config = config;
        this._logger = logger ?? NullLogger.Instance;
        this._delayProvider = delayProvider ?? new TaskDelayProvider();
        this._timeProvider = timeProvider ?? new DefaultTimeProvider();
    }

    /// <summary>
    /// Executes the action with retry logic
    /// </summary>
    /// <remarks>
    /// The request is retried if it throws an exception that is a retryable exception.
    /// If the request throws an exception that is not a retryable exception, it is not retried.
    /// If the request returns a response with a retryable error code, it is retried.
    /// If the request returns a response with a non-retryable error code, it is not retried.
    /// If the exception contains a RetryAfter header, the request is retried after the specified delay.
    /// If configured to use exponential backoff, the delay is doubled for each retry.
    /// </remarks>
    /// <param name="request">The request.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        int retryCount = 0;

        var start = this._timeProvider.GetCurrentTime();
        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();

            TimeSpan waitFor;
            string reason;
            HttpResponseMessage? response = null;
            try
            {
                response = await base.SendAsync(request, cancellationToken).ConfigureAwait(false);

                // If the request does not require a retry then we're done
                if (!this.ShouldRetry(response.StatusCode))
                {
                    return response;
                }

                reason = response.StatusCode.ToString();

                // If the retry count is greater than the max retry count then we'll
                // just return
                if (retryCount >= this._config.MaxRetryCount)
                {
                    this._logger.LogError(
                        "Error executing request, max retry count reached. Reason: {0}", reason);
                    return response;
                }

                // If the retry delay is longer than the total timeout, then we'll
                // just return
                if (!this.HasTimeForRetry(start, retryCount, response, out waitFor))
                {
                    var timeTaken = this._timeProvider.GetCurrentTime() - start;
                    this._logger.LogError(
                        "Error executing request, max total retry time reached. Reason: {0}. Time spent: {1}ms", reason,
                        timeTaken.TotalMilliseconds);
                    return response;
                }
            }
            catch (Exception e) when (this.ShouldRetry(e) || this.ShouldRetry(e.InnerException))
            {
                reason = e.GetType().ToString();
                if (retryCount >= this._config.MaxRetryCount)
                {
                    this._logger.LogError(e,
                        "Error executing request, max retry count reached. Reason: {0}", reason);
                    throw;
                }
                else if (!this.HasTimeForRetry(start, retryCount, response, out waitFor))
                {
                    var timeTaken = this._timeProvider.GetCurrentTime() - start;
                    this._logger.LogError(
                        "Error executing request, max total retry time reached. Reason: {0}. Time spent: {1}ms", reason,
                        timeTaken.TotalMilliseconds);
                    throw;
                }
            }

            // If the request requires a retry then we'll retry
            this._logger.LogWarning(
                "Error executing action [attempt {0} of {1}]. Reason: {2}. Will retry after {3}ms",
                retryCount + 1,
                this._config.MaxRetryCount,
                reason,
                waitFor.TotalMilliseconds);

            // Increase retryCount
            retryCount++;

            response?.Dispose();

            // Delay
            await this._delayProvider.DelayAsync(waitFor, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Interface for a delay provider, primarily to enable unit testing.
    /// </summary>
    internal interface IDelayProvider
    {
        Task DelayAsync(TimeSpan delay, CancellationToken cancellationToken);
    }

    internal sealed class TaskDelayProvider : IDelayProvider
    {
        public Task DelayAsync(TimeSpan delay, CancellationToken cancellationToken)
        {
            return Task.Delay(delay, cancellationToken);
        }
    }

    /// <summary>
    /// Interface for a time provider, primarily to enable unit testing.
    /// </summary>
    internal interface ITimeProvider
    {
        DateTimeOffset GetCurrentTime();
    }

    internal sealed class DefaultTimeProvider : ITimeProvider
    {
        public DateTimeOffset GetCurrentTime()
        {
            return DateTimeOffset.UtcNow;
        }
    }

    private readonly HttpRetryConfig _config;
    private readonly ILogger _logger;
    private readonly IDelayProvider _delayProvider;
    private readonly ITimeProvider _timeProvider;

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

        // If exponential backoff is enabled, double the delay for each retry
        if (this._config.UseExponentialBackoff)
        {
            for (var backoffRetryCount = 1; backoffRetryCount < retryCount + 1; backoffRetryCount++)
            {
                timeToWait = timeToWait.Add(timeToWait);
            }
        }

        return timeToWait;
    }

    /// <summary>
    /// Determines if there is time left for a retry.
    /// </summary>
    /// <param name="start">The start time of the original request.</param>
    /// <param name="retryCount">The current retry count.</param>
    /// <param name="response">The response message that potentially contains RetryAfter header.</param>
    /// <param name="waitFor">The wait time for the next retry.</param>
    /// <returns>True if there is time left for a retry, false otherwise.</returns>
    private bool HasTimeForRetry(DateTimeOffset start, int retryCount, HttpResponseMessage? response, out TimeSpan waitFor)
    {
        waitFor = this.GetWaitTime(retryCount, response);
        var currentTIme = this._timeProvider.GetCurrentTime();
        var result = currentTIme - start + waitFor;

        return result < this._config.MaxTotalRetryTime;
    }

    private bool ShouldRetry(HttpStatusCode statusCode)
    {
        return this._config.RetryableStatusCodes.Contains(statusCode);
    }

    private bool ShouldRetry(Exception? exception)
    {
        return exception != null && this._config.RetryableExceptionTypes.Contains(exception.GetType());
    }
}
