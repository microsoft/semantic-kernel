// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.CoreSkills;
/// <summary>
/// MathSkill provides a set of functions to make Math calculations.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("math", new MathSkill());
/// Examples:
/// {{math.Sum}}         => Returns the sum of FirstNumber and SecondNumber (provided in the SKContext)
/// </example>
public class MathSkill
{
    /// <summary>
    /// Returns the Addition result of initial and amount values provided.
    /// </summary>
    /// <param name="initialValue">Initial value to add the specified amount</param>
    /// <param name="context">Contains the context to get the numbers from</param>
    /// <returns>The resulting sum as a string.</returns>
    [SKFunction("Adds value to a value")]
    [SKFunctionName("Add")]
    [SKFunctionInput(Description = "The value to add")]
    [SKFunctionContextParameter(Name = "Amount", Description = "Amount to add")]
    public async Task<string> AddAsync(string initialValue, SKContext context)
    {
#pragma warning disable CA1806
        int.TryParse(initialValue, out var targetValue);
#pragma warning restore CA1806

        var amount = int.Parse(context["Amount"], CultureInfo.InvariantCulture);

        var result = targetValue + amount;

        return await Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
    }

    /// <summary>
    /// Returns the Sum of two SKContext numbers provided.
    /// </summary>
    /// <param name="initialValue">Initial value to subtract the specified amount</param>
    /// <param name="context">Contains the context to get the numbers from</param>
    /// <returns>The resulting substraction as a string.</returns>
    [SKFunction("Subtracts value to a value")]
    [SKFunctionName("Subtract")]
    [SKFunctionInput(Description = "The value to subtract")]
    [SKFunctionContextParameter(Name = "Amount", Description = "Amount to subtract")]
    public async Task<string> SubtractAsync(string initialValue, SKContext context)
    {
#pragma warning disable CA1806
        int.TryParse(initialValue, out var targetValue);
#pragma warning restore CA1806

        var amount = int.Parse(context["Amount"], CultureInfo.InvariantCulture);

        var result = targetValue - amount;

        return await Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
    }
}
