// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planners.Handlebars;
using RepoUtils;

/**
 * This example shows how to use multiple prompt template formats.
 */
// ReSharper disable once InconsistentNaming
public static class Example65_HandlebarsPlanner
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"======== {nameof(Example65_HandlebarsPlanner)} ========");

        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .Build();

        kernel.ImportFunctions(new DictionaryPlugin(), DictionaryPlugin.PluginName);

        var planner = new HandlebarsPlanner(kernel);

        var goal = "Teach me a new word!";
        var plan = await planner.CreatePlanAsync(goal);

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan);

        var result = plan.Invoke(kernel.CreateNewContext(), new Dictionary<string, object?>(), CancellationToken.None);

        Console.WriteLine("Result:");
        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Plugin example with two native functions, where one function gets a random word and the other returns a definition for a given word.
    /// </summary>
    private sealed class DictionaryPlugin
    {
        public const string PluginName = nameof(DictionaryPlugin);

        private readonly Dictionary<string, string> _dictionary = new()
        {
            {"apple", "a round fruit with red, green, or yellow skin and a white flesh"},
            {"book", "a set of printed or written pages bound together along one edge"},
            {"cat", "a small furry animal with whiskers and a long tail that is often kept as a pet"},
            {"dog", "a domesticated animal with four legs, a tail, and a keen sense of smell that is often used for hunting or companionship"},
            {"elephant", "a large gray mammal with a long trunk, tusks, and ears that lives in Africa and Asia"}
        };

        [SKFunction, SKName("GetRandomWord"), System.ComponentModel.Description("Gets a random word from a dictionary of common words and their definitions.")]
        public string GetRandomWord()
        {
            // Get random number
            var index = RandomNumberGenerator.GetInt32(0, this._dictionary.Count - 1);

            // Return the word at the random index
            return this._dictionary.ElementAt(index).Key;
        }

        [SKFunction, SKName("GetDefintion"), System.ComponentModel.Description("Gets the definition for a given word.")]
        public string GetDefintion([System.ComponentModel.Description("Word to get definition for.")] string word)
        {
            return this._dictionary.TryGetValue(word, out var definition)
                ? definition
                : "Word not found";
        }
    }
}
