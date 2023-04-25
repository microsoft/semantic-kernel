// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using RepoUtils;
using Skills;

// ReSharper disable once InconsistentNaming
public static class Example04_BingSkill
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Bing Skill And Adapter ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Load skills
        var textSkill = kernel.ImportSkill(new TextSkill());

        using var bing = new BingAdapter(Env.Var("BING_API_KEY"));
        var bingWebSearch = new WebSearchEngineSkill(bing);
        var bingSkill = kernel.ImportSkill(bingWebSearch);

        // Run
        var ask = "What's the tallest building in Europe?";
        var result = await kernel.RunAsync(
            ask,
            textSkill["Uppercase"],
            bingSkill["SearchAsync"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine(result);
    }
}
