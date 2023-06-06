// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.SkillDefinition;

// ReSharper disable once InconsistentNaming
public static class Example01_NativeFunctions
{
    public static void Run()
    {
        Console.WriteLine("======== Functions ========");

        // Load native skill
        var text = new Example01_MyTextSkill();

        // Use function without kernel
        var result = text.Uppercase("ciao!");

        Console.WriteLine(result);
    }
}

public class Example01_MyTextSkill
{
    [SKFunction("Change all string chars to uppercase")]
    [SKFunctionInput(Description = "Text to uppercase")]
    public string Uppercase(string input)
    {
        return input.ToUpperInvariant();
    }
}
