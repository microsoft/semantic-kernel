// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Amazon.Runtime;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.Handlebars;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Plugins;
using Plugins.DictionaryPlugin;
using RepoUtils;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using System.Reflection;
using Microsoft.CodeAnalysis.Emit;
using System.Linq;
using System.Collections.Generic;
using NRedisStack;
using MongoDB.Driver.GeoJsonObjectModel;
using System.Text.RegularExpressions;
using Microsoft.CodeAnalysis.CSharp.Syntax;

/**
 * This example shows how to use the Handlebars sequential planner.
 */
public static class Example999_HandlebarsPlanner
{
    private static int s_sampleIndex;

    private const string CourseraPluginName = "CourseraPlugin";

    /// <summary>
    /// Show how to create a plan with Handlebars and execute it.
    /// </summary>
    public static async Task RunAsync()
    {
        s_sampleIndex = 1;
        bool shouldPrintPrompt = true;

        // Using primitive types as inputs and outputs

        await DynamicSKillSampleAsync();
        //await RunDictionaryWithBasicTypesSampleAsync();
        //await RunPoetrySampleAsync();
        //await RunBookSampleAsync();

        // Using Complex Types as inputs and outputs
        //await RunLocalDictionaryWithComplexTypesSampleAsync(shouldPrintPrompt);
    }

    private static void WriteSampleHeadingToConsole(string name)
    {
        Console.WriteLine($"======== [Handlebars Planner] Sample {s_sampleIndex++} - Create and Execute {name} Plan ========");
    }

    private static async Task RunSampleAsync(string goal, bool shouldPrintPrompt = false, params string[] pluginDirectoryNames)
    {
        //string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        //string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        //string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        //string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        //if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        //{
        //    Console.WriteLine("Azure endpoint, apiKey, deploymentName, or modelId not found. Skipping example.");
        //    return;
        //}

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        //var gplugin = KernelPluginFactory.CreateFromType<GeneratedPlugin>();
        //kernel.Plugins.Add(gplugin);

        //var kernel = new KernelBuilder()
        //    .AddAzureOpenAIChatCompletion(
        //        deploymentName: chatDeploymentName,
        //        modelId: chatModelId,
        //        endpoint: endpoint,
        //        serviceId: "AzureOpenAIChat",
        //        apiKey: apiKey)
        //    .Build();

        if (pluginDirectoryNames[0] == StringParamsDictionaryPlugin.PluginName)
        {
            kernel.ImportPluginFromType<StringParamsDictionaryPlugin>(StringParamsDictionaryPlugin.PluginName);
        }
        else if (pluginDirectoryNames[0] == ComplexParamsDictionaryPlugin.PluginName)
        {
            kernel.ImportPluginFromType<ComplexParamsDictionaryPlugin>(ComplexParamsDictionaryPlugin.PluginName);
        }
        else if (pluginDirectoryNames[0] == CourseraPluginName)
        {
            await kernel.ImportPluginFromOpenApiAsync(
                CourseraPluginName,
                new Uri("https://www.coursera.org/api/rest/v1/search/openapi.yaml")
            );
        }
        else
        {
            string folder = RepoFiles.SamplePluginsPath();

            foreach (var pluginDirectoryName in pluginDirectoryNames)
            {
                kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, pluginDirectoryName));
            }
        }

        // Use gpt-4 or newer models if you want to test with loops. 
        // Older models like gpt-35-turbo are less recommended. They do handle loops but are more prone to syntax errors.
        var allowLoopsInPlan = true; // chatDeploymentName.Contains("gpt-4", StringComparison.OrdinalIgnoreCase);
        var planner = new HandlebarsPlanner(
            new HandlebarsPlannerConfig()
            {
                // Change this if you want to test with loops regardless of model selection.
                AllowLoops = allowLoopsInPlan
            });

        Console.WriteLine($"Goal: {goal}");

        // Create the plan
        var plan = await planner.CreatePlanAsync(kernel, goal);

        // Print the prompt template
        if (shouldPrintPrompt)
        {
            Console.WriteLine($"\nPrompt template:\n{plan.Prompt}");
        }

        Console.WriteLine($"\nOriginal plan:\n{plan}");

        // Execute the plan
        var result = await plan.InvokeAsync(kernel, new KernelArguments(), CancellationToken.None);
        Console.WriteLine($"\nResult:\n{result}\n");
    }

    private static async Task RunSamplePluginClassAsync(string goal, bool shouldPrintPrompt = false, KernelPlugin? kp = null)
    {
        //string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        //string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        //string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        //string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        //if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        //{
        //    Console.WriteLine("Azure endpoint, apiKey, deploymentName, or modelId not found. Skipping example.");
        //    return;
        //}

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        //var gplugin = KernelPluginFactory.CreateFromType<GeneratedPlugin>();
        //kernel.Plugins.Add(gplugin);

        if (kp != null)
        {
            kernel.Plugins.Add(kp);
        }

        // Use gpt-4 or newer models if you want to test with loops. 
        // Older models like gpt-35-turbo are less recommended. They do handle loops but are more prone to syntax errors.
        var allowLoopsInPlan = true; // chatDeploymentName.Contains("gpt-4", StringComparison.OrdinalIgnoreCase);
        var planner = new HandlebarsPlanner(
            new HandlebarsPlannerConfig()
            {
                // Change this if you want to test with loops regardless of model selection.
                AllowLoops = allowLoopsInPlan
            });

        Console.WriteLine($"Goal: {goal}");

        // Create the plan
        var plan = await planner.CreatePlanAsync(kernel, goal);

        // Print the prompt template
        if (shouldPrintPrompt)
        {
            Console.WriteLine($"\nPrompt template:\n{plan.Prompt}");
        }

        Console.WriteLine($"\nOriginal plan:\n{plan}");

        // Execute the plan
        var result = await plan.InvokeAsync(kernel, new KernelArguments(), CancellationToken.None);
        Console.WriteLine($"\nResult:\n{result}\n");
    }

    private static async Task DynamicSKillSampleAsync(bool shouldPrintPrompt = false)
    {
        KernelPlugin kp = null;
        bool needMorePlugins = true;
        while (needMorePlugins)
        {
            WriteSampleHeadingToConsole("DynamicSkillSample");
            try
            {
                // Load additional plugins to enable planner but not enough for the given goal.
                string testPrompt = @"

How big are the files combined in C:\\Temp folder? Tell me the size in MB and the number of files.
                ";
                await RunSamplePluginClassAsync(testPrompt, shouldPrintPrompt, kp);
                needMorePlugins = false;
            }
            catch (KernelException e)
            {
                Console.WriteLine($"{e.Message.Split("Planner output:")[1]}\n");
                string input = e.Message;
                string code = input.Substring(input.IndexOf("```csharp") + "```csharp".Length, input.IndexOf("```", input.IndexOf("```csharp") + "```csharp".Length) - input.IndexOf("```csharp") - "```csharp".Length);
                if (code.Contains("Assemblies required"))
                {
                    code = input.Substring(input.IndexOf("```csharp") + "```csharp".Length, input.IndexOf("Assemblies required", input.IndexOf("```csharp") + "```csharp".Length) - input.IndexOf("```csharp") - "```csharp".Length);
                }
                string[] lines = input.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

                List<string> assemblies = new List<string>();

                bool startAdding = false;

                foreach (string line in lines)
                {
                    if (line.Contains("Assemblies required"))
                    {
                        startAdding = true;
                        continue;
                    }

                    if (startAdding && line.StartsWith("- "))
                    {
                        assemblies.Add(line.Substring(2));
                    }
                }

                SyntaxTree syntaxTree = CSharpSyntaxTree.ParseText(code);
                string directory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);

                // Get all .dll files in the directory
                string[] files = Directory.GetFiles(directory, "*.dll");

                // Create a list to hold the filenames
                List<string> filenames = new List<string>();

                List<MetadataReference> references = new List<MetadataReference>();

                references.Add(MetadataReference.CreateFromFile(typeof(object).GetTypeInfo().Assembly.Location));
                references.Add(MetadataReference.CreateFromFile(typeof(System.ComponentModel.BrowsableAttribute).Assembly.Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("System.Runtime, Version=7.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a").Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("netstandard, Version = 2.0.0.0, Culture = neutral, PublicKeyToken = cc7b13ffcd2ddd51").Location));
                references.Add(MetadataReference.CreateFromFile(Assembly.Load("System.Collections, Version=7.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a").Location));

                //foreach (string assembly in assemblies)
                //{
                //    if (!assembly.Contains("SemanticKernel"))
                //        references.Add(MetadataReference.CreateFromFile(Assembly.Load(assembly).Location));
                //}

                foreach (string file in files)
                {
                    references.Add(MetadataReference.CreateFromFile(file));
                }

                Console.WriteLine("Compiling Generated Kernel Plugin");

                CSharpCompilation compilation = CSharpCompilation.Create(
                    "assemblyName",
                    syntaxTrees: new[] { syntaxTree },
                    references: references.ToArray(),
                    options: new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

                using (var ms = new MemoryStream())
                {
                    EmitResult result = compilation.Emit(ms);

                    if (!result.Success)
                    {
                        // handle exceptions
                        Console.WriteLine("Compilation failed");
                        foreach (var x in result.Diagnostics)
                        {
                            Console.WriteLine(x.GetMessage());
                        }
                        Console.ReadKey(); return;
                    }
                    else
                    {
                        ms.Seek(0, SeekOrigin.Begin);
                        Assembly assembly = Assembly.Load(ms.ToArray());

                        // Get the type from the assembly
                        Type pluginType = assembly.GetType("Plugins.GeneratedPlugin");

                        // Create an instance of the type
                        var instance = Activator.CreateInstance(pluginType);

                        Console.WriteLine("Adding plugin to kernel. Restarting planner.");

                        Type factoryType = typeof(KernelPluginFactory);
                        MethodInfo method = factoryType.GetMethod("CreateFromType");
                        MethodInfo genericMethod = method.MakeGenericMethod(pluginType);
                        string param = "GeneratedPlugin";
                        object[] parameters = { param, null };

                        kp = (KernelPlugin)genericMethod.Invoke(null, parameters);
                        //kp = instance;
                    }
                }

                needMorePlugins = true;
            }
        }
    }
    private static async Task PlanNotPossibleSampleAsync(bool shouldPrintPrompt = false)
    {
        WriteSampleHeadingToConsole("Plan Not Possible");

        try
        {
            // Load additional plugins to enable planner but not enough for the given goal.
            await RunSampleAsync("Send Mary an email with the list of meetings I have scheduled today.", shouldPrintPrompt, "SummarizePlugin");
        }
        catch (KernelException e)
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

    private static async Task RunDictionaryWithBasicTypesSampleAsync(bool shouldPrintPrompt = false)
    {
        WriteSampleHeadingToConsole("Dictionary");
        await RunSampleAsync("Get a random word and its definition.", shouldPrintPrompt, StringParamsDictionaryPlugin.PluginName);
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

    private static async Task RunLocalDictionaryWithComplexTypesSampleAsync(bool shouldPrintPrompt = false)
    {
        WriteSampleHeadingToConsole("Complex Types with Local Dictionary Plugin");
        await RunSampleAsync("Teach me two random words and their definition.", shouldPrintPrompt, ComplexParamsDictionaryPlugin.PluginName);
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

    private static async Task RunPoetrySampleAsync(bool shouldPrintPrompt = false)
    {
        WriteSampleHeadingToConsole("Poetry");
        await RunSampleAsync("Write a poem about John Doe, then translate it into Italian.", shouldPrintPrompt, "SummarizePlugin", "WriterPlugin");
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

    private static async Task RunBookSampleAsync(bool shouldPrintPrompt = false)
    {
        WriteSampleHeadingToConsole("Book Creation");
        await RunSampleAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'", shouldPrintPrompt, "WriterPlugin", "MiscPlugin");
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
}
