// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Configuration;

namespace Microsoft.SemanticKernel.Reliability;

internal sealed class DefaultHttpRetryHandler : DelegatingHandler
{
    /// <summary>
    /// Initializes a new instance of the <see cref="DefaultHttpRetryHandler"/> class.
    /// </summary>
    /// <param name="config">The retry configuration.</param>
    /// <param name="log">The logger.</param>
    public DefaultHttpRetryHandler(KernelConfig.HttpRetryConfig? config = null, ILogger? log = null) : this(config ?? new KernelConfig.HttpRetryConfig(), log,
        null, null)
    {
    }

    public readonly Guid Id = Guid.NewGuid();

    internal DefaultHttpRetryHandler(KernelConfig.HttpRetryConfig config, ILogger? log = null, IDelayProvider? delayProvider = null,
        ITimeProvider? timeProvider = null)
    {
        this._config = config;
        this._log = log ?? NullLogger.Instance;
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

            TimeSpan waitFor = default;
            string reason = string.Empty;
            HttpResponseMessage? response = null;
            try
            {
                response = await base.SendAsync(request, cancellationToken);

                // If the request does not require a retry then we're done
                if (!this.ShouldRetry(response.StatusCode))
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

                reason = response.StatusCode.ToString();

                if (retryCount >= this._config.MaxRetryCount)
                {
                    this._log.LogError(
                        "Error executing request, max retry count reached. Reason: {0}", reason);
                    return response;
                }

                // If the retry delay is longer than the total timeout, then we'll
                // just return
                if (!this.HasTimeForRetry(start, retryCount, response, out waitFor))
                {
                    this._log.LogError(
                        "Error executing request, max total retry time reached. Reason: {0}", reason);
                    return response;
                }
            }
            catch (Exception e) when ((this.ShouldRetry(e) || this.ShouldRetry(e.InnerException)) &&
                                      retryCount < this._config.MaxRetryCount &&
                                      this.HasTimeForRetry(start, retryCount, response, out waitFor))
            {
                reason = e.GetType().ToString();
            }

            // If the request requires a retry then we'll retry
            this._log.LogWarning(
                "Error executing action [attempt {0} of {1}]. Reason: {2}. Will retry after {3}ms",
                retryCount + 1,
                this._config.MaxRetryCount,
                reason,
                waitFor.TotalMilliseconds);

            // Clone request with CloneAsync before retrying
            // Do not dispose this request as that breaks the request cloning
#pragma warning disable CA2000
            request = await CloneAsync(request);
#pragma warning restore CA2000

            // Increase retryCount
            retryCount++;

            // Delay
            await this._delayProvider.DelayAsync(waitFor, cancellationToken).ConfigureAwait(false);
        }
    }

    private TimeSpan GetWaitTime(int retryCount, HttpResponseMessage? response)
    {
        var retryAfter = response?.Headers.RetryAfter?.Date.HasValue == true
            ? response?.Headers.RetryAfter?.Date - DateTimeOffset.Now
            : (response?.Headers.RetryAfter?.Delta) ?? this._config.MinRetryDelay;
        retryAfter ??= this._config.MinRetryDelay;

        var timeToWait = retryAfter > this._config.MaxRetryDelay
            ? this._config.MaxRetryDelay
            : retryAfter < this._config.MinRetryDelay
                ? this._config.MinRetryDelay
                : retryAfter ?? default;

        if (this._config.UseExponentialBackoff)
        {
            for (var backoffRetryCount = 1; backoffRetryCount < retryCount + 1; backoffRetryCount++)
            {
                timeToWait = timeToWait.Add(timeToWait);
            }
        }

        return timeToWait;
    }

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

    private bool ShouldRetry(Exception exception)
    {
        return this._config.RetryableExceptionTypes.Contains(exception.GetType());
    }

    /// <summary>
    /// Create a new HTTP request by copying previous HTTP request's headers and properties from response's request message.
    /// Copied from: https://github.com/microsoftgraph/msgraph-sdk-dotnet-core/blob/dev/src/Microsoft.Graph.Core/Extensions/HttpRequestMessageExtensions.cs
    /// </summary>
    /// <param name="originalRequest">The previous <see cref="HttpRequestMessage"/> needs to be copy.</param>
    /// <returns>The <see cref="HttpRequestMessage"/>.</returns>
    /// <remarks>
    /// Re-issue a new HTTP request with the previous request's headers and properties
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
        foreach (var property in originalRequest.Properties)
        {
            newRequest.Properties.Add(property);
        }

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
            }, TaskScheduler.Current).ConfigureAwait(false);

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

    private readonly KernelConfig.HttpRetryConfig _config;
    private readonly ILogger _log;
    private readonly IDelayProvider _delayProvider;
    private readonly ITimeProvider _timeProvider;

    internal interface IDelayProvider
    {
        Task DelayAsync(TimeSpan delay, CancellationToken cancellationToken);
    }

    internal class TaskDelayProvider : IDelayProvider
    {
        public async Task DelayAsync(TimeSpan delay, CancellationToken cancellationToken)
        {
            await Task.Delay(delay, cancellationToken);
        }
    }

    internal interface ITimeProvider
    {
        DateTimeOffset GetCurrentTime();
    }

    internal class DefaultTimeProvider : ITimeProvider
    {
        public DateTimeOffset GetCurrentTime()
        {
            return DateTimeOffset.UtcNow;
        }
    }
}
