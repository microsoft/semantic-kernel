// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
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
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, openAIApiKey)
            .Build();

        string bingApiKey = TestConfiguration.Bing.ApiKey;
        if (bingApiKey == null)
        {
            Console.WriteLine("Bing credentials not found. Skipping example.");
            return;
        }

        var bingConnector = new BingConnector(bingApiKey);
        var bing = new WebSearchEnginePlugin(bingConnector);
        var search = kernel.ImportPlugin(bing, "bing");

        // Load semantic plugins defined with prompt templates
        string folder = RepoFiles.SamplePluginsPath();

        var summarizePlugin = kernel.ImportSemanticPluginFromDirectory(folder, "SummarizePlugin");

        // Run
        var ask = "What's the tallest building in South America";

        var result1 = await kernel.RunAsync(
            ask,
            search["Search"]
        );

        var result2 = await kernel.RunAsync(
            ask,
            search["Search"],
            summarizePlugin["Summarize"]
        );

        var result3 = await kernel.RunAsync(
            ask,
            search["Search"],
            summarizePlugin["Notegen"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine("Bing Answer: " + result1 + "\n");
        Console.WriteLine("Summary: " + result2 + "\n");
        Console.WriteLine("Notes: " + result3 + "\n");
    }
}
