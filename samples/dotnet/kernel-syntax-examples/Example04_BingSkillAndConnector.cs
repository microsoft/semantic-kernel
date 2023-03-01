// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using RepoUtils;
using Skills;

// ReSharper disable once InconsistentNaming
public static class Example04_BingSkillAndConnector
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== BingSkillAndConnector ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Load skills
        var textSkill = kernel.ImportSkill(new TextSkill());

        using var bingConnector = new BingConnector(Env.Var("BING_API_KEY"));
        var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);
        var web = kernel.ImportSkill(webSearchEngineSkill);

        // Run
        var ask = "What's the tallest building in Europe?";
        var result = await kernel.RunAsync(
            ask,
            textSkill["Uppercase"],
            web["SearchAsync"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine(result);
    }
}
