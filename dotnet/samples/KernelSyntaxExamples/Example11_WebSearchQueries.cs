// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Skills.Web;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example11_WebSearchQueries
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== WebSearchQueries ========");

        IKernel kernel = Kernel.Builder.WithLogger(ConsoleLogger.Logger).Build();

        // Load native skills
        var skill = new SearchUrlSkill();
        var bing = kernel.ImportSkill(skill, "search");

        // Run
        var ask = "What's the tallest building in Europe?";
        var result = await kernel.RunAsync(
            ask,
            bing["BingSearchUrl"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine(result);
    }
}
