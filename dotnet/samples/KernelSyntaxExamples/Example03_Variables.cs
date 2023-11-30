// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Plugins;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example03_Variables
{
    private static readonly ILoggerFactory s_loggerFactory = ConsoleLogger.LoggerFactory;

    public static async Task RunAsync()
    {
        Console.WriteLine("======== Variables ========");

        Kernel kernel = new KernelBuilder().WithLoggerFactory(s_loggerFactory).Build();
        var textPlugin = kernel.ImportPluginFromObject<StaticTextPlugin>();

        var arguments = new KernelFunctionArguments
        {
            ["input"] = "Today is: ",
            ["day"] = DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture)
        };

        var result = await kernel.InvokeAsync(textPlugin["AppendDay"], arguments);

        Console.WriteLine(result.GetValue<string>());
    }
}
