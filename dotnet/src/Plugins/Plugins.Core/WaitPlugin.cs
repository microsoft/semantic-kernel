// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// WaitPlugin provides a set of functions to wait before making the rest of operations.
/// </summary>
public sealed class WaitPlugin
{
    private readonly TimeProvider _timeProvider;

    /// <summary>
    /// Initializes a new instance of the <see cref="WaitPlugin"/> class.
    /// </summary>
    public WaitPlugin() : this(null) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="WaitPlugin"/> class.
    /// </summary>
    /// <param name="timeProvider">An optional time provider. If not provided, a default time provider will be used.</param>
    [ActivatorUtilitiesConstructor]
    public WaitPlugin(TimeProvider? timeProvider = null) =>
        this._timeProvider = timeProvider ?? TimeProvider.System;

    /// <summary>
    /// Wait a given amount of seconds
    /// </summary>
    /// <example>
    /// {{wait.seconds 10}} (Wait 10 seconds)
    /// </example>
    [KernelFunction, Description("Wait a given amount of seconds")]
    public Task SecondsAsync([Description("The number of seconds to wait")] decimal seconds) =>
        this._timeProvider.Delay(TimeSpan.FromSeconds((double)Math.Max(seconds, 0)));
}
