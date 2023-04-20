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
/// {{math.Add}}         => Returns the sum of FirstNumber and SecondNumber (provided in the SKContext)
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
    public Task<string> AddAsync(string initialValueText, SKContext context) =>
        AddOrSubtractAsync(initialValueText, context, add: true);

    /// <summary>
    /// Returns the Sum of two SKContext numbers provided.
    /// </summary>
    /// <param name="initialValueText">Initial value as string to subtract the specified amount</param>
    /// <param name="context">Contains the context to get the numbers from</param>
    /// <returns>The resulting subtraction as a string.</returns>
    [SKFunction("Subtracts value to a value")]
    [SKFunctionName("Subtract")]
    [SKFunctionInput(Description = "The value to subtract")]
    [SKFunctionContextParameter(Name = "Amount", Description = "Amount to subtract")]
    public Task<string> SubtractAsync(string initialValueText, SKContext context) =>
        AddOrSubtractAsync(initialValueText, context, add: false);

    private static Task<string> AddOrSubtractAsync(string initialValueText, SKContext context, bool add)
    {
        if (!int.TryParse(initialValueText, NumberStyles.Any, CultureInfo.InvariantCulture, out var initialValue))
        {
            return Task.FromException<string>(new ArgumentOutOfRangeException(nameof(initialValueText), initialValueText, "Initial value provided is not in numeric format"));
        }

        string contextAmount = context["Amount"];
        if (!int.TryParse(contextAmount, NumberStyles.Any, CultureInfo.InvariantCulture, out var amount))
        {
            return Task.FromException<string>(new ArgumentOutOfRangeException(nameof(context), contextAmount, "Context amount provided is not in numeric format"));
        }

        var result = add ?
            initialValue + amount :
            initialValue - amount;

        return Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
    }
}
