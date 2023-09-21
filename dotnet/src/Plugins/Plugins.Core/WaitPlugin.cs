// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// WaitPlugin provides a set of functions to wait before making the rest of operations.
/// </summary>
/// <example>
/// Usage: kernel.ImportPlugin("wait", new WaitPlugin());
/// Examples:
/// {{wait.seconds 10}}         => Wait 10 seconds
/// </example>
public sealed class WaitPlugin
{
    private readonly IWaitProvider _waitProvider;

    /// <summary>
    /// Interface for providing wait functionality.
    /// </summary>
    public interface IWaitProvider
    {
        /// <summary>
        /// Delays the execution for a specified number of milliseconds.
        /// </summary>
        /// <param name="milliSeconds">The number of milliseconds to wait.</param>
        /// <returns>A task that represents the asynchronous delay operation.</returns>
        Task DelayAsync(int milliSeconds);
    }

    private sealed class WaitProvider : IWaitProvider
    {
        public Task DelayAsync(int milliSeconds)
        {
            return Task.Delay(milliSeconds);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WaitPlugin"/> class.
    /// </summary>
    /// <param name="waitProvider">An optional wait provider. If not provided, a default wait provider will be used.</param>
    public WaitPlugin(IWaitProvider? waitProvider = null)
    {
        this._waitProvider = waitProvider ?? new WaitProvider();
    }

    /// <summary>
    /// Wait a given amount of seconds
    /// </summary>
    /// <example>
    /// {{wait.seconds 10}} (Wait 10 seconds)
    /// </example>
    [SKFunction, Description("Wait a given amount of seconds")]
    public async Task SecondsAsync([Description("The number of seconds to wait")] decimal seconds)
    {
        var milliseconds = seconds * 1000;
        milliseconds = milliseconds > 0 ? milliseconds : 0;

        await this._waitProvider.DelayAsync((int)milliseconds).ConfigureAwait(false);
    }
}
