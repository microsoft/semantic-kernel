// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;
using Skills;

// ReSharper disable once InconsistentNaming
public static class Example03_Variables
{
    private static readonly ILogger s_logger = ConsoleLogger.Logger;

    public static async Task RunAsync()
    {
        Console.WriteLine("======== Variables ========");

        IKernel kernel = new KernelBuilder().WithLogger(s_logger).Build();
        var text = kernel.ImportSkill(new StaticTextSkill(), "text");

        var variables = new ContextVariables("Today is: ");
        variables.Set("day", DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture));

        SKContext result = await kernel.RunAsync(variables,
            text["AppendDay"],
            text["Uppercase"]);

        Console.WriteLine(result);
    }
}
