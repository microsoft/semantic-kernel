// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.CoreSkills;

/// <summary>
/// WaitSkill provides a set of functions to wait before making the rest of operations.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("wait", new WaitSkill());
/// Examples:
/// {{wait.seconds 10}}         => Wait 10 seconds
/// </example>
public class WaitSkill
{
    private readonly IWaitProvider _waitProvider;

    public interface IWaitProvider
    {
        Task DelayAsync(int milliSeconds);
    }

    private class WaitProvider : IWaitProvider
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
    [SKFunction("Wait a given amount of seconds")]
    [SKFunctionName("Seconds")]
    [SKFunctionInput(DefaultValue = "0", Description = "The number of seconds to wait")]
    public async Task SecondsAsync(string secondsText)
    {
        if (!decimal.TryParse(secondsText, NumberStyles.Any, CultureInfo.InvariantCulture, out var seconds))
        {
            throw new ArgumentException("Seconds provided is not in numeric format", nameof(secondsText));
        }

        var milliseconds = seconds * 1000;
        milliseconds = (milliseconds > 0) ? milliseconds : 0;

        await this._waitProvider.DelayAsync((int)milliseconds);
    }
}
