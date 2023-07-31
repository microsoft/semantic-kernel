// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Plugins.MathPlugin;

public class Math
{
    [SKFunction, Description("Take the square root of a number")]
    public string Sqrt(string number)
    {
        return System.Math.Sqrt(Convert.ToDouble(number, CultureInfo.InvariantCulture)).ToString(CultureInfo.InvariantCulture);
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
}
