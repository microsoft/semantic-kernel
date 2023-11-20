// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Planning.Handlebars;
using RepoUtils;

/**
 * This example shows how to use the Handlebars sequential planner.
 */
public static class Example65_HandlebarsPlanner
{
    private static int s_sampleCount;

    /// <summary>
    /// Show how to create a plan with Handlebars and execute it.
    /// </summary>
    public static async Task RunAsync()
    {
        s_sampleCount = 0;
        Console.WriteLine($"======== {nameof(Example65_HandlebarsPlanner)} ========");

        await PlanNotPossibleSampleAsync();
        await RunDictionarySampleAsync();
        await RunPoetrySampleAsync();
        await RunBookSampleAsync();
    }

    private static void WriteSampleHeadingToConsole(string name)
    {
        Console.WriteLine($"======== [Handlebars Planner] Sample {s_sampleCount++} - Create and Execute {name} Plan ========");
    }

    private static async Task RunSampleAsync(string goal, params string[] pluginDirectoryNames)
    {
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

        if (pluginDirectoryNames[0] == DictionaryPlugin.PluginName)
        {
            kernel.ImportPluginFromObject(new DictionaryPlugin(), DictionaryPlugin.PluginName);
        }
        else
        {
            string folder = RepoFiles.SamplePluginsPath();

            foreach (var pluginDirectoryName in pluginDirectoryNames)
            {
                kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, pluginDirectoryName));
            }
        }

        // The gpt-35-turbo model does not handle loops well in the plans.
        var allowLoopsInPlan = chatDeploymentName.Contains("gpt-35-turbo", StringComparison.OrdinalIgnoreCase) ? false : true;

        var planner = new HandlebarsPlanner(kernel, new HandlebarsPlannerConfig() { AllowLoops = allowLoopsInPlan });
        Console.WriteLine($"Goal: {goal}");

        // Create the plan
        var plan = await planner.CreatePlanAsync(goal);
        Console.WriteLine($"\nOriginal plan:\n{plan}");

        // Execute the plan
        var result = plan.Invoke(kernel.CreateNewContext(), new Dictionary<string, object?>(), CancellationToken.None);
        Console.WriteLine($"\nResult:\n{result.GetValue<string>()}\n");
    }

    private static async Task PlanNotPossibleSampleAsync()
    {
        WriteSampleHeadingToConsole("Plan Not Possible");

        try
        {
            // Load additional plugins to enable planner but not enough for the given goal.
            await RunSampleAsync("Send Mary an email with the list of meetings I have scheduled today.", "SummarizePlugin");
        }
        catch (SKException e)
        {
            /*
                Unable to create plan for goal with available functions.
                Goal: Email me a list of meetings I have scheduled today.
                Available Functions: SummarizePlugin-Notegen, SummarizePlugin-Summarize, SummarizePlugin-MakeAbstractReadable, SummarizePlugin-Topics
                Planner output:
                I'm sorry, but it seems that the provided helpers do not include any helper to fetch or filter meetings scheduled for today. 
                Therefore, I cannot create a Handlebars template to achieve the specified goal with the available helpers. 
                Additional helpers may be required.
            */
            Console.WriteLine($"{e.Message}\n");
        }
    }

    private static async Task RunDictionarySampleAsync()
    {
        WriteSampleHeadingToConsole("Dictionary");
        await RunSampleAsync("Get a random word and its definition.", DictionaryPlugin.PluginName);
        /*
            Original plan:
            {{!-- Step 1: Get a random word --}}
            {{set "randomWord" (DictionaryPlugin-GetRandomWord)}}

            {{!-- Step 2: Get the definition of the random word --}}
            {{set "definition" (DictionaryPlugin-GetDefinition word=(get "randomWord"))}}

            {{!-- Step 3: Output the random word and its definition --}}
            {{json (array (get "randomWord") (get "definition"))}}

            Result:
            ["book","a set of printed or written pages bound together along one edge"]
        */
    }

    private static async Task RunPoetrySampleAsync()
    {
        WriteSampleHeadingToConsole("Poetry");
        await RunSampleAsync("Write a poem about John Doe, then translate it into Italian.", "SummarizePlugin", "WriterPlugin");
        /*
            Original plan:
            {{!-- Step 1: Initialize the scenario for the poem --}}
            {{set "scenario" "John Doe, a mysterious and kind-hearted person"}}

            {{!-- Step 2: Generate a short poem about John Doe --}}
            {{set "poem" (WriterPlugin-ShortPoem input=(get "scenario"))}}

            {{!-- Step 3: Translate the poem into Italian --}}
            {{set "translatedPoem" (WriterPlugin-Translate input=(get "poem") language="Italian")}}

            {{!-- Step 4: Output the translated poem --}}
            {{json (get "translatedPoem")}}

            Result:
            C'era una volta un uomo di nome John Doe,
            La cui gentilezza si mostrava costantemente,
            Aiutava con un sorriso,
            E non si arrendeva mai,
            Al mistero che lo faceva brillare.
        */
    }

    private static async Task RunBookSampleAsync()
    {
        WriteSampleHeadingToConsole("Book Creation");
        await RunSampleAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'", "WriterPlugin", "MiscPlugin");
        /*
            Original plan:
            {{!-- Step 1: Initialize the book title and chapter count --}}
            {{set "bookTitle" "The Thinking Caps"}}
            {{set "chapterCount" 3}}

            {{!-- Step 2: Generate the novel outline with the given chapter count --}}
            {{set "novelOutline" (WriterPlugin-NovelOutline input=(get "bookTitle") chapterCount=(get "chapterCount"))}}

            {{!-- Step 3: Loop through the chapters and generate the content for each chapter --}}
            {{#each (range 1 (get "chapterCount"))}}
                {{set "chapterIndex" this}}
                {{set "chapterSynopsis" (MiscPlugin-ElementAtIndex input=(get "novelOutline") index=(get "chapterIndex"))}}
                {{set "previousChapterSynopsis" (MiscPlugin-ElementAtIndex input=(get "novelOutline") index=(get "chapterIndex" - 1))}}
                
                {{!-- Step 4: Write the chapter content using the WriterPlugin-NovelChapter helper --}}
                {{set "chapterContent" (WriterPlugin-NovelChapter input=(get "chapterSynopsis") theme=(get "bookTitle") previousChapter=(get "previousChapterSynopsis") chapterIndex=(get "chapterIndex"))}}
                
                {{!-- Step 5: Output the chapter content --}}
                {{json (get "chapterContent")}}
            {{/each}}
        */
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

        [SKFunction, SKName("GetDefinition"), System.ComponentModel.Description("Gets the definition for a given word.")]
        public string GetDefinition([System.ComponentModel.Description("Word to get definition for.")] string word)
        {
            return this._dictionary.TryGetValue(word, out var definition)
                ? definition
                : "Word not found";
        }
    }
}
