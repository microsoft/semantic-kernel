// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Reliability.Basic;

/// <summary>
/// Retry configuration for DefaultKernelRetryHandler that uses RetryAfter header when present.
/// </summary>
public sealed record BasicRetryConfig
{
    /// <summary>
    /// Maximum number of retries.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when value is negative.</exception>
    public int MaxRetryCount
    {
        get => this._maxRetryCount;
        set
        {
            if (value < 0)
            {
                throw new ArgumentOutOfRangeException(nameof(this.MaxRetryCount), "Max retry count cannot be negative.");
            }

            this._maxRetryCount = value;
        }
    }

    /// <summary>
    /// Minimum delay between retries.
    /// </summary>
    public TimeSpan MinRetryDelay { get; set; } = TimeSpan.FromSeconds(2);

    /// <summary>
    /// Maximum delay between retries.
    /// </summary>
    public TimeSpan MaxRetryDelay { get; set; } = TimeSpan.FromSeconds(60);

    /// <summary>
    /// Maximum total time spent retrying.
    /// </summary>
    public TimeSpan MaxTotalRetryTime { get; set; } = TimeSpan.FromMinutes(2);

    /// <summary>
    /// Whether to use exponential backoff or not.
    /// </summary>
    public bool UseExponentialBackoff { get; set; }

    /// <summary>
    /// List of status codes that should be retried.
    /// </summary>
    public List<HttpStatusCode> RetryableStatusCodes { get; set; } = new()
    {
        (HttpStatusCode)HttpStatusCodeType.RequestTimeout,
        (HttpStatusCode)HttpStatusCodeType.ServiceUnavailable,
        (HttpStatusCode)HttpStatusCodeType.GatewayTimeout,
        (HttpStatusCode)HttpStatusCodeType.TooManyRequests,
        (HttpStatusCode)HttpStatusCodeType.BadGateway,
    };

    /// <summary>
    /// List of exception types that should be retried.
    /// </summary>
    public List<Type> RetryableExceptionTypes { get; set; } = new()
    {
        typeof(HttpRequestException)
    };

    private int _maxRetryCount = 1;
}
