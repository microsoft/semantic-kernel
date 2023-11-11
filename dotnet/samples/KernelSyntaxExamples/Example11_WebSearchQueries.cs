// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example11_WebSearchQueries
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== WebSearchQueries ========");

        IKernel kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        // Load native plugins
        var plugin = new SearchUrlPlugin();
        var bing = kernel.ImportFunctions(plugin, "search");

        // Run
        var ask = "What's the tallest building in Europe?";
        var result = await kernel.RunAsync(
            ask,
            bing["BingSearchUrl"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine(result.GetValue<string>());
    }
}
