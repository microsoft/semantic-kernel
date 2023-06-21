// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Orchestration;
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
        var text = kernel.ImportSkill(new TextSkill());

        SKContext result = await kernel.RunAsync("    i n f i n i t e     s p a c e     ",
            text["TrimStart"],
            text["TrimEnd"],
            text["Uppercase"]);

        Console.WriteLine(result);
    }
}
