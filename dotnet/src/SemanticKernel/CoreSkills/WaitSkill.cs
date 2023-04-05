// Copyright (c) Microsoft. All rights reserved.

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
    /// <summary>
    /// Wait a given ammount of seconds
    /// </summary>
    /// <example>
    /// {{wait.seconds 10}} (Wait 10 seconds)
    /// </example>
    [SKFunction("Wait a given amount of seconds")]
    [SKFunctionName("Seconds")]
    [SKFunctionInput(DefaultValue = "0", Description = "The number of seconds to wait")]
    public async Task SecondsAsync(string secondsText)
    {
        await Task.Delay(int.Parse(secondsText, CultureInfo.InvariantCulture));
    }
}
