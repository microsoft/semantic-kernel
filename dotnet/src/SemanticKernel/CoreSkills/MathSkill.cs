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
    /// Returns the Sum of two SKContext numbers provided.
    /// </summary>
    /// <param name="context">Contains the context to get the numbersFrom</param>
    /// <returns>The resulting sum as a string.</returns>
    [SKFunction("Returns the sum of two values")]
    [SKFunctionName("Sum")]
    [SKFunctionContextParameter(Name = "FirstNumber", Description = "The first number to make the sum")]
    [SKFunctionContextParameter(Name = "SecondNumber", Description = "The second number to make the sum")]
    public async Task<string> SumAsync(SKContext context)
    {
        var targetValue = int.Parse(context["FirstNumber"], CultureInfo.InvariantCulture);
        var amount = int.Parse(context["SecondNumber"], CultureInfo.InvariantCulture);

        var result = targetValue + amount;

        return await Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
    }

    /// <summary>
    /// Returns the Sum of two SKContext numbers provided.
    /// </summary>
    /// <param name="context">Contains the context to get the numbersFrom</param>
    /// <returns>The resulting sum as a string.</returns>
    [SKFunction("Adds value to an existing")]
    [SKFunctionName("Add")]
    [SKFunctionContextParameter(Name = "Target", Description = "The target variable to add")]
    [SKFunctionContextParameter(Name = "Amount", Description = "Amount to add")]
    public async Task<SKContext> AddAsync(SKContext context)
    {
        var targetValue = int.Parse(context[context["Target"]], CultureInfo.InvariantCulture);
        var amount = int.Parse(context["Amount"], CultureInfo.InvariantCulture);

        var result = targetValue + amount;

        context[context["Target"]] = result.ToString(CultureInfo.InvariantCulture);

        return await Task.FromResult(context);
    }
}
