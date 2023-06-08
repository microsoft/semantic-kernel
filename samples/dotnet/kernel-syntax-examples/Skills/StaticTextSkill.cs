// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130

namespace Skills;

[SuppressMessage("Design", "CA1052:Type is a static holder type but is neither static nor NotInheritable",
    Justification = "Static classes are not currently supported by the semantic kernel.")]
public class StaticTextSkill
{
    [SKFunction("Change all string chars to uppercase")]
    [SKFunctionInput(Description = "Text to uppercase")]
    public static string Uppercase(string input)
    {
        return input.ToUpperInvariant();
    }

    [SKFunction("Append the day variable")]
    [SKFunctionInput(Description = "Text to append to")]
    [SKFunctionContextParameter(Name = "day", Description = "Value of the day to append")]
    public static string AppendDay(string input, SKContext context)
    {
        return input + context["day"];
    }
}
