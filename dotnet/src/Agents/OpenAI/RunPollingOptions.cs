﻿// Copyright (c) Microsoft. All rights reserved.
using System;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Configuration and defaults associated with polling behavior for Assistant API run processing.
/// </summary>
public sealed class RunPollingOptions
{
    /// <summary>
    /// The default polling interval when monitoring thread-run status.
    /// </summary>
    public static TimeSpan DefaultPollingInterval { get; } = TimeSpan.FromMilliseconds(500);

    /// <summary>
    /// The default back-off interval when  monitoring thread-run status.
    /// </summary>
    public static TimeSpan DefaultPollingBackoff { get; } = TimeSpan.FromSeconds(1);

    /// <summary>
    /// The default number of polling iterations before using <see cref="RunPollingBackoff"/>.
    /// </summary>
    public static int DefaultPollingBackoffThreshold { get; } = 2;

    /// <summary>
    /// The default polling delay when retrying message retrieval due to a 404/NotFound from synchronization lag.
    /// </summary>
    public static TimeSpan DefaultMessageSynchronizationDelay { get; } = TimeSpan.FromMilliseconds(500);

    /// <summary>
    /// The polling interval when monitoring thread-run status.
    /// </summary>
    public TimeSpan RunPollingInterval { get; set; } = DefaultPollingInterval;

    /// <summary>
    /// The back-off interval when  monitoring thread-run status.
    /// </summary>
    public TimeSpan RunPollingBackoff { get; set; } = DefaultPollingBackoff;

    /// <summary>
    /// The number of polling iterations before using <see cref="RunPollingBackoff"/>.
    /// </summary>
    public int RunPollingBackoffThreshold { get; set; } = DefaultPollingBackoffThreshold;

    /// <summary>
    /// The polling delay when retrying message retrieval due to a 404/NotFound from synchronization lag.
    /// </summary>
    public TimeSpan MessageSynchronizationDelay { get; set; } = DefaultMessageSynchronizationDelay;

    /// <summary>
    /// Gets the polling interval for the specified iteration count.
    /// </summary>
    /// <param name="iterationCount">The number of polling iterations already attempted</param>
    public TimeSpan GetPollingInterval(int iterationCount) =>
        iterationCount > this.RunPollingBackoffThreshold ? this.RunPollingBackoff : this.RunPollingInterval;
}
