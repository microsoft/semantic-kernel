// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Core;

// ReSharper disable once InconsistentNaming
public static class Example01_NativeFunctions
{
    public static Task RunAsync()
    {
        Console.WriteLine("======== Functions ========");

        // Load native skill
        var text = new TextSkill();

        // Use function without kernel
        var result = text.Uppercase("ciao!");

        Console.WriteLine(result);

        return Task.CompletedTask;
    }
}
