// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example04_CombineLLMPromptsAndNativeCode
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== LLMPrompts ========");

        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Logger)
            .WithOpenAITextCompletionService("text-davinci-002", openAIApiKey, serviceId: "text-davinci-002")
            .WithOpenAITextCompletionService("text-davinci-003", openAIApiKey)
            .Build();

        // Load native skill
        string bingApiKey = TestConfiguration.Bing.ApiKey;

        if (bingApiKey == null)
        {
            Console.WriteLine("Bing credentials not found. Skipping example.");
            return;
        }

        var bingConnector = new BingConnector(bingApiKey);
        var bing = new WebSearchEngineSkill(bingConnector);
        var search = kernel.ImportSkill(bing, "bing");

        // Load semantic skill defined with prompt templates
        string folder = RepoFiles.SampleSkillsPath();

        var sumSkill = kernel.ImportSemanticSkillFromDirectory(
            folder,
            "SummarizeSkill");

        // Run
        var ask = "What's the tallest building in South America";

        var result1 = await kernel.RunAsync(
            ask,
            search["Search"]
        );

        var result2 = await kernel.RunAsync(
            ask,
            search["Search"],
            sumSkill["Summarize"]
        );

        var result3 = await kernel.RunAsync(
            ask,
            search["Search"],
            sumSkill["Notegen"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine("Bing Answer: " + result1 + "\n");
        Console.WriteLine("Summary: " + result2 + "\n");
        Console.WriteLine("Notes: " + result3 + "\n");
    }
}
