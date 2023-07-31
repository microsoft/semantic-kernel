// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Plugins.MathPlugin;

public class Math
{
    [SKFunction, Description("Take the square root of a number")]
    public string Sqrt(string input)
    {
        return System.Math.Sqrt(Convert.ToDouble(input, CultureInfo.InvariantCulture)).ToString(CultureInfo.InvariantCulture);
    }

    [SKFunction, Description("Add two numbers")]
    [SKParameter("input", "The first number to add")]
    [SKParameter("number2", "The second number to add")]
    public string Add(SKContext context)
    {
        return (
            Convert.ToDouble(context.Variables["input"], CultureInfo.InvariantCulture) +
            Convert.ToDouble(context.Variables["number2"], CultureInfo.InvariantCulture)
        ).ToString(CultureInfo.InvariantCulture);
    }

    [SKFunction, Description("Subtract two numbers")]
    [SKParameter("input", "The first number to subtract from")]
    [SKParameter("number2", "The second number to subtract away")]
    public string Subtract(SKContext context)
    {
        return (
            Convert.ToDouble(context.Variables["input"], CultureInfo.InvariantCulture) -
            Convert.ToDouble(context.Variables["number2"], CultureInfo.InvariantCulture)
        ).ToString(CultureInfo.InvariantCulture);
    }

    [SKFunction, Description("Multiply two numbers. When increasing by a percentage, don't forget to add 1 to the percentage.")]
    [SKParameter("input", "The first number to multiply")]
    [SKParameter("number2", "The second number to multiply")]
    public string Multiply(SKContext context)
    {
        return (
            Convert.ToDouble(context.Variables["input"], CultureInfo.InvariantCulture) *
            Convert.ToDouble(context.Variables["number2"], CultureInfo.InvariantCulture)
        ).ToString(CultureInfo.InvariantCulture);
    }

    [SKFunction, Description("Divide two numbers")]
    [SKParameter("input", "The first number to divide from")]
    [SKParameter("number2", "The second number to divide by")]
    public string Divide(SKContext context)
    {
        return (
            Convert.ToDouble(context.Variables["input"], CultureInfo.InvariantCulture) /
            Convert.ToDouble(context.Variables["number2"], CultureInfo.InvariantCulture)
        ).ToString(CultureInfo.InvariantCulture);
    }
}
