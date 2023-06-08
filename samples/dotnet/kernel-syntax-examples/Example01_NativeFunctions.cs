// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.CoreSkills;

// ReSharper disable once InconsistentNaming
public static class Example01_NativeFunctions
{
    public static void Run()
    {
        Console.WriteLine("======== Functions ========");

        // Load native skill
        var text = new TextSkill();

        // Use function without kernel
        var result = text.Uppercase("ciao!");

        Console.WriteLine(result);
    }
}
