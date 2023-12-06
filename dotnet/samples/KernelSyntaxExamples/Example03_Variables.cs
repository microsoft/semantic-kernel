// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Plugins;

// ReSharper disable once InconsistentNaming
public static class Example03_Variables
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Variables ========");

        Kernel kernel = new();
        var textPlugin = kernel.ImportPluginFromType<StaticTextPlugin>();

        var arguments = new KernelArguments("Today is: ")
        {
            ["day"] = DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture)
        };

        var result = await kernel.InvokeAsync(textPlugin["AppendDay"], arguments);

        Console.WriteLine(result.GetValue<string>());
    }
}
