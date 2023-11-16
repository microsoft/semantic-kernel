// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Planners.Handlebars;
using RepoUtils;

/**
 * This example shows how to use the Handlebars sequential planner with complex types.
 */
public static class Example66_HandlebarsPlannerWithComplexTypes
{
    private static int s_sampleCount;

    /// <summary>
    /// Show how to create a plan with Handlebars and execute it.
    /// </summary>
    public static async Task RunAsync()
    {
        s_sampleCount = 0;
        Console.WriteLine($"======== {nameof(Example66_HandlebarsPlannerWithComplexTypes)} ========");
        await RunLocalDictionarySampleAsync();
        await RunRemoteDictionarySampleAsync();
    }

    private static void WriteSampleHeadingToConsole(string name)
    {
        Console.WriteLine($"======== [Handlebars Planner] Sample {s_sampleCount++} - Create and Execute {name} Plan ========");
    }

    private static async Task RunSampleAsync(string goal, bool useLocalPlugin = true)
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

        if (useLocalPlugin)
        {
            kernel.ImportFunctions(new DictionaryPlugin(), DictionaryPlugin.PluginName);
        }
        else
        {
            await kernel.ImportOpenApiPluginFunctionsAsync(
                DictionaryPlugin.PluginName,
                "./Plugins/DictionaryPlugin/openapi.json",
                new OpenApiFunctionExecutionParameters()
            );
        }

        var planner = new HandlebarsPlanner(kernel);
        Console.WriteLine($"Goal: {goal}");

        // Create the plan
        var plan = await planner.CreatePlanAsync(goal);
        Console.WriteLine($"\nOriginal plan:\n{plan}");

        // Execute the plan
        var result = plan.Invoke(kernel.CreateNewContext(), new Dictionary<string, object?>(), CancellationToken.None);
        Console.WriteLine($"\nResult:\n{result.GetValue<string>()}\n");
    }

    private static async Task RunLocalDictionarySampleAsync()
    {
        WriteSampleHeadingToConsole("Local Dictionary");
        await RunSampleAsync("Teach me two random words and their definition.");
        /*
            Original Plan:
            {{!-- Step 1: Get two random dictionary entries --}}
            {{set "entry1" (DictionaryPlugin-GetRandomEntry)}}
            {{set "entry2" (DictionaryPlugin-GetRandomEntry)}}

            {{!-- Step 2: Extract words from the entries --}}
            {{set "word1" (DictionaryPlugin-GetWord entry=(get "entry1"))}}
            {{set "word2" (DictionaryPlugin-GetWord entry=(get "entry2"))}}

            {{!-- Step 3: Extract definitions for the words --}}
            {{set "definition1" (DictionaryPlugin-GetDefinition word=(get "word1"))}}
            {{set "definition2" (DictionaryPlugin-GetDefinition word=(get "word2"))}}

            {{!-- Step 4: Display the words and their definitions --}}
            Word 1: {{json (get "word1")}}
            Definition: {{json (get "definition1")}}

            Word 2: {{json (get "word2")}}
            Definition: {{json (get "definition2")}}

            Result:
            Word 1: apple
            Definition 1: a round fruit with red, green, or yellow skin and a white flesh

            Word 2: dog
            Definition 2: a domesticated animal with four legs, a tail, and a keen sense of smell that is often used for hunting or companionship
        */
    }

    private static async Task RunRemoteDictionarySampleAsync()
    {
        WriteSampleHeadingToConsole("Remote Dictionary");

        try
        {
            await RunSampleAsync("Teach me two random words and their definition.", false);
        }
        catch (InvalidOperationException)
        {
            // TODO (@teresaqhoang): Get a better remote plugin to test with.
            // Expected `no server-url` error, plugin isn't actually hosted. Was testing to see how complex types render in template. 
            Console.WriteLine($"======== DONE {nameof(Example66_HandlebarsPlannerWithComplexTypes)} ========");
        }
    }

    /// <summary>
    /// Plugin example with two Local functions, where one function gets a random word and the other returns a definition for a given word.
    /// </summary>
    private sealed class DictionaryPlugin
    {
        public const string PluginName = nameof(DictionaryPlugin);

        private readonly List<DictionaryEntry> _dictionary = new()
        {
            new DictionaryEntry("apple", "a round fruit with red, green, or yellow skin and a white flesh"),
            new DictionaryEntry("book", "a set of printed or written pages bound together along one edge"),
            new DictionaryEntry("cat", "a small furry animal with whiskers and a long tail that is often kept as a pet"),
            new DictionaryEntry("dog", "a domesticated animal with four legs, a tail, and a keen sense of smell that is often used for hunting or companionship"),
            new DictionaryEntry("elephant", "a large gray mammal with a long trunk, tusks, and ears that lives in Africa and Asia")
        };

        [SKFunction, SKName("GetRandomEntry"), System.ComponentModel.Description("Gets a random word from a dictionary of common words and their definitions.")]
        public DictionaryEntry GetRandomEntry()
        {
            // Get random number
            var index = RandomNumberGenerator.GetInt32(0, this._dictionary.Count - 1);

            // Return the word at the random index
            return this._dictionary[index];
        }

        [SKFunction, SKName("GetWord"), System.ComponentModel.Description("Gets the word for a given dictionary entry.")]
        public string GetWord([System.ComponentModel.Description("Word to get definition for.")] DictionaryEntry entry)
        {
            // Return the definition or a default message
            return this._dictionary.FirstOrDefault(e => e.Word == entry.Word)?.Word ?? "Entry not found";
        }

        [SKFunction, SKName("GetDefinition"), System.ComponentModel.Description("Gets the definition for a given word.")]
        public string GetDefinition([System.ComponentModel.Description("Word to get definition for.")] string word)
        {
            // Return the definition or a default message
            return this._dictionary.FirstOrDefault(e => e.Word == word)?.Definition ?? "Word not found";
        }
    }

    #region Custom Type

    /// <summary>
    /// In order to use custom types, <see cref="TypeConverter"/> should be specified,
    /// that will convert object instance to string representation.
    /// </summary>
    /// <remarks>
    /// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
    /// it can be passed to AI for further processing using semantic functions.
    /// It's possible to choose any format (e.g. XML, JSON, YAML) to represent your object.
    /// </remarks>
    [TypeConverter(typeof(DictionaryEntryConverter))]
    public sealed class DictionaryEntry
    {
        public string Word { get; set; } = string.Empty;
        public string Definition { get; set; } = string.Empty;

        public DictionaryEntry(string word, string definition)
        {
            this.Word = word;
            this.Definition = definition;
        }
    }

    /// <summary>
    /// Implementation of <see cref="TypeConverter"/> for <see cref="DictionaryEntry"/>.
    /// In this example, object instance is serialized with <see cref="JsonSerializer"/> from System.Text.Json,
    /// but it's possible to convert object to string using any other serialization logic.
    /// </summary>
#pragma warning disable CA1812 // instantiated by Kernel
    private sealed class DictionaryEntryConverter : TypeConverter
#pragma warning restore CA1812
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        /// <summary>
        /// This method is used to convert object from string to actual type. This will allow to pass object to
        /// Local function which requires it.
        /// </summary>
        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<DictionaryEntry>((string)value);
        }

        /// <summary>
        /// This method is used to convert actual type to string representation, so it can be passed to AI
        /// for further processing.
        /// </summary>
        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }

    #endregion
}
