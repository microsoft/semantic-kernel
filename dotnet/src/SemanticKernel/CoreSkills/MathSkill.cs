// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

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
    /// <param name="initialValueText">Initial value as string to add the specified amount</param>
    /// <param name="context">Contains the context to get the numbers from</param>
    /// <returns>The resulting sum as a string.</returns>
    [SKFunction("Adds value to a value")]
    [SKFunctionName("Add")]
    [SKFunctionInput(Description = "The value to add")]
    [SKFunctionContextParameter(Name = "Amount", Description = "Amount to add")]
    public async Task<string> AddAsync(string initialValueText, SKContext context)
    {
        (int initialValue, int amount) = Validate(initialValueText, context);

        var result = initialValue + amount;

        return await Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
    }

    /// <summary>
    /// Returns the Sum of two SKContext numbers provided.
    /// </summary>
    /// <param name="initialValueText">Initial value as string to subtract the specified amount</param>
    /// <param name="context">Contains the context to get the numbers from</param>
    /// <returns>The resulting substraction as a string.</returns>
    [SKFunction("Subtracts value to a value")]
    [SKFunctionName("Subtract")]
    [SKFunctionInput(Description = "The value to subtract")]
    [SKFunctionContextParameter(Name = "Amount", Description = "Amount to subtract")]
    public async Task<string> SubtractAsync(string initialValueText, SKContext context)
    {
        (int initialValue, int amount) = Validate(initialValueText, context);

        var result = initialValue - amount;

        return await Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
    }

    private static (int initialValue, int amount) Validate(string initialValueText, SKContext context)
    {
        if (!int.TryParse(initialValueText, NumberStyles.Any, CultureInfo.InvariantCulture, out var initialValue))
        {
            throw new ArgumentException("Initial value provided is not in numeric format", nameof(initialValueText));
        }

        if (!int.TryParse(context["Amount"], NumberStyles.Any, CultureInfo.InvariantCulture, out var amount))
        {
            throw new ArgumentException("Context amount provided is not in numeric format", nameof(context));
        }

        return (initialValue, amount);
    }
}
