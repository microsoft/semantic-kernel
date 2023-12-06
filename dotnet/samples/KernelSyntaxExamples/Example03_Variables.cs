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

        var arguments = new KernelArguments("Today is: ")
        {
            ["day"] = DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture)
        };

        // ** Different ways of executing function with arguments **

        // Specify and get the value type as generic parameter
        var resultValue = await kernel.InvokeAsync<string>(textPlugin["AppendDay"], arguments);
        Console.WriteLine($"string -> {resultValue}");

        // If you need to access the result metadata, you can use the non-generic version to get the FunctionResult
        var functionResult = await kernel.InvokeAsync(textPlugin["AppendDay"], arguments);
        var metadata = functionResult.Metadata;

        // Specify the type from the FunctionResult
        Console.WriteLine($"FunctionResult.GetValue<string>() -> {functionResult.GetValue<string>()}");

        // FunctionResult.ToString() automatically converts the result to string
        Console.WriteLine($"FunctionResult.ToString() -> {functionResult}");
    }
}
