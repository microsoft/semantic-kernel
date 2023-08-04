// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example21_ChatGptPlugins
{
    public static async Task RunAsync()
    {
        await RunChatGptPluginAsync();
    }

    private static async Task RunChatGptPluginAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Logger).Build();
        using HttpClient httpClient = new();

        //Import a ChatGPT plugin via URI
        var skill = await kernel.ImportAIPluginAsync("<skill name>", new Uri("<chatGPT-plugin>"), new OpenApiSkillExecutionParameters(httpClient));

        //Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("<parameter-name>", "<parameter-value>");

        //Run
        var result = await kernel.RunAsync(contextVariables, skill["productsUsingGET"]);

        Console.WriteLine("Skill execution result: {0}", result);
        Console.ReadLine();

        //--------------- Example of using Klarna ChatGPT plugin ------------------------

        //var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Logger).Build();

        //var skill = await kernel.ImportAIPluginAsync("Klarna", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), new OpenApiSkillExecutionParameters(httpClient));

        //var contextVariables = new ContextVariables();
        //contextVariables.Set("q", "Laptop");      // A precise query that matches one very small category or product that needs to be searched for to find the products the user is looking for. If the user explicitly stated what they want, use that as a query. The query is as specific as possible to the product name or category mentioned by the user in its singular form, and don't contain any clarifiers like latest, newest, cheapest, budget, premium, expensive or similar. The query is always taken from the latest topic, if there is a new topic a new query is started.
        //contextVariables.Set("size", "3");        // number of products returned
        //contextVariables.Set("budget", "200");    // maximum price of the matching product in local currency, filters results
        //contextVariables.Set("countryCode", "US");// ISO 3166 country code with 2 characters based on the user location. Currently, only US, GB, DE, SE and DK are supported.

        //var result = await kernel.RunAsync(contextVariables, skill["productsUsingGET"]);

        //Console.WriteLine("Klarna skill response: {0}", result);
        //Console.ReadLine();
    }
}
