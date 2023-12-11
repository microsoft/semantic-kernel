// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Plugins;

/*
 * This example shows how to use kernel arguments when invoking functions.
 */
// ReSharper disable once InconsistentNaming
public static class Example03_Arguments
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Arguments ========");

        Kernel kernel = new();
        var textPlugin = kernel.ImportPluginFromType<StaticTextPlugin>();

        var arguments = new KernelArguments()
        {
            ["input"] = "Today is: ",
            ["day"] = DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture)
        };

        // ** Different ways of executing functions with arguments **

        // Specify and get the value type as generic parameter
        string? resultValue = await kernel.InvokeAsync<string>(textPlugin["AppendDay"], arguments);
        Console.WriteLine($"string -> {resultValue}");

        // If you need to access the result metadata, you can use the non-generic version to get the FunctionResult
        FunctionResult functionResult = await kernel.InvokeAsync(textPlugin["AppendDay"], arguments);
        var metadata = functionResult.Metadata;

        // Specify the type from the FunctionResult
        Console.WriteLine($"FunctionResult.GetValue<string>() -> {functionResult.GetValue<string>()}");

        // FunctionResult.ToString() automatically converts the result to string
        Console.WriteLine($"FunctionResult.ToString() -> {functionResult}");
    }
}
