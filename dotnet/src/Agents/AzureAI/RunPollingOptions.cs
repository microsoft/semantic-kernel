// Copyright (c) Microsoft. All rights reserved.
using System;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Configuration and defaults associated with polling behavior for Assistant API run processing.
/// </summary>
public sealed class RunPollingOptions
{
    /// <summary>
    /// Gets the default maximum number of retries when monitoring thread-run status.
    /// </summary>
    public static int DefaultMaximumRetryCount { get; } = 3;

    /// <summary>
    /// Gets the default polling interval when monitoring thread-run status.
    /// </summary>
    public static TimeSpan DefaultPollingInterval { get; } = TimeSpan.FromMilliseconds(500);

    /// <summary>
    /// Gets the default back-off interval when monitoring thread-run status.
    /// </summary>
    public static TimeSpan DefaultPollingBackoff { get; } = TimeSpan.FromSeconds(1);

    /// <summary>
    /// Gets the default number of polling iterations before using <see cref="RunPollingBackoff"/>.
    /// </summary>
    public static int DefaultPollingBackoffThreshold { get; } = 2;

    /// <summary>
    /// Gets the default polling delay when retrying message retrieval due to a 404/NotFound from synchronization lag.
    /// </summary>
    public static TimeSpan DefaultMessageSynchronizationDelay { get; } = TimeSpan.FromMilliseconds(500);

    /// <summary>
    /// Gets or sets the maximum retry count when polling thread-run status.
    /// </summary>
    /// <remarks>
    /// This value only affects failures that have the potential to be transient.
    /// Explicit server error responses will result in immediate failure.
    /// </remarks>
    public int MaximumRetryCount { get; set; } = DefaultMaximumRetryCount;

    /// <summary>
    /// Gets or sets the polling interval when monitoring thread-run status.
    /// </summary>
    public TimeSpan RunPollingInterval { get; set; } = DefaultPollingInterval;

    /// <summary>
    /// Gets or sets the back-off interval when monitoring thread-run status.
    /// </summary>
    public TimeSpan RunPollingBackoff { get; set; } = DefaultPollingBackoff;

    /// <summary>
    /// Gets or sets the number of polling iterations before using <see cref="RunPollingBackoff"/>.
    /// </summary>
    public int RunPollingBackoffThreshold { get; set; } = DefaultPollingBackoffThreshold;

    /// <summary>
    /// Gets or sets the polling delay when retrying message retrieval due to a 404/NotFound from synchronization lag.
    /// </summary>
    public TimeSpan MessageSynchronizationDelay { get; set; } = DefaultMessageSynchronizationDelay;

    /// <summary>
    /// Gets the polling interval for the specified iteration count.
    /// </summary>
    /// <param name="iterationCount">The number of polling iterations already attempted.</param>
    public TimeSpan GetPollingInterval(int iterationCount)
    {
        return iterationCount > this.RunPollingBackoffThreshold ? this.RunPollingBackoff : this.RunPollingInterval;
    }
}
