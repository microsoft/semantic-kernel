// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130

namespace ExampleSkills;

public class TextSkill
{
    [SKFunction("Remove spaces to the left of a string")]
    [SKFunctionInput(Description = "Text to edit")]
    public string LStrip(string input)
    {
        return input.TrimStart();
    }

    [SKFunction("Remove spaces to the right of a string")]
    [SKFunctionInput(Description = "Text to edit")]
    public string RStrip(string input)
    {
        return input.TrimEnd();
    }

    [SKFunction("Remove spaces to the left and right of a string")]
    [SKFunctionInput(Description = "Text to edit")]
    public string Strip(string input)
    {
        return input.Trim();
    }

    [SKFunction("Change all string chars to uppercase")]
    [SKFunctionInput(Description = "Text to uppercase")]
    public string Uppercase(string input)
    {
        return input.ToUpperInvariant();
    }

    [SKFunction("Change all string chars to lowercase")]
    [SKFunctionInput(Description = "Text to lowercase")]
    [SuppressMessage("Globalization", "CA1308:Normalize strings to uppercase", Justification = "By design.")]
    public string Lowercase(string input)
    {
        return input.ToLowerInvariant();
    }
}
