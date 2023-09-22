// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.Core;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example02_Pipeline
{
    private static readonly ILoggerFactory s_loggerFactory = ConsoleLogger.LoggerFactory;

    public static async Task RunAsync()
    {
        Console.WriteLine("======== Pipeline ========");

        IKernel kernel = new KernelBuilder().WithLoggerFactory(s_loggerFactory).Build();

        // Load native plugin
        var text = kernel.ImportPlugin(new TextPlugin());

        SKContext result = await kernel.RunAsync("    i n f i n i t e     s p a c e     ",
            text["TrimStart"],
            text["TrimEnd"],
            text["Uppercase"]);

        Console.WriteLine(result);
    }
}
