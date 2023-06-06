// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example02_Pipeline
{
    private static readonly ILogger s_log = ConsoleLogger.Log;

    public static async Task RunAsync()
    {
        Console.WriteLine("======== Pipeline ========");

        IKernel kernel = new KernelBuilder().WithLogger(s_log).Build();

        // Load native skill
        var text = kernel.ImportSkill(new Example02_MyTextSkill());

        SKContext result = await kernel.RunAsync("    i n f i n i t e     s p a c e     ",
            text["LStrip"],
            text["RStrip"],
            text["Uppercase"]);

        Console.WriteLine(result);
    }
}

public class Example02_MyTextSkill
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

    [SKFunction("Change all string chars to uppercase")]
    [SKFunctionInput(Description = "Text to uppercase")]
    public string Uppercase(string input)
    {
        return input.ToUpperInvariant();
    }
}
