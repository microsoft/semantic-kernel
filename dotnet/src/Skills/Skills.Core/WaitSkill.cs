// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Core;

/// <summary>
/// WaitSkill provides a set of functions to wait before making the rest of operations.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("wait", new WaitSkill());
/// Examples:
/// {{wait.seconds 10}}         => Wait 10 seconds
/// </example>
public sealed class WaitSkill
{
    private readonly IWaitProvider _waitProvider;

    public interface IWaitProvider
    {
        Task DelayAsync(int milliSeconds);
    }

    private sealed class WaitProvider : IWaitProvider
    {
        public Task DelayAsync(int milliSeconds)
        {
            return Task.Delay(milliSeconds);
        }
    }

    public WaitSkill(IWaitProvider? waitProvider = null)
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
