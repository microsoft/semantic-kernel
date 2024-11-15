﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Planning.Handlebars;
using Plugins.DictionaryPlugin;
using Resources;
using xRetry;

namespace Planners;

// This example shows how to use the Handlebars sequential planner.
public class HandlebarsPlanning(ITestOutputHelper output) : BaseTest(output)
{
    private static int s_sampleIndex;

    private const string CourseraPluginName = "CourseraPlugin";

    private void WriteSampleHeading(string name)
    {
        Console.WriteLine($"======== [Handlebars Planner] Sample {s_sampleIndex++} - Create and Execute Plan with: {name} ========");
    }

    private async Task<Kernel?> SetupKernelAsync(params string[] pluginDirectoryNames)
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey is null || chatDeploymentName is null || chatModelId is null || endpoint is null)
        {
            Console.WriteLine("Azure endpoint, apiKey, deploymentName, or modelId not found. Skipping example.");
            return null;
        }

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey,
                modelId: chatModelId)
            .Build();

        if (pluginDirectoryNames.Length > 0)
        {
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
        }

        return kernel;
    }

    private void PrintPlannerDetails(string goal, HandlebarsPlan plan, string result, bool shouldPrintPrompt)
    {
        Console.WriteLine($"Goal: {goal}");
        Console.WriteLine($"\nOriginal plan:\n{plan}");
        Console.WriteLine($"\nResult:\n{result}\n");

        // Print the prompt template
        if (shouldPrintPrompt && plan.Prompt is not null)
        {
            Console.WriteLine("\n======== CreatePlan Prompt ========");
            Console.WriteLine(plan.Prompt);
        }
    }

    private async Task RunSampleAsync(
        string goal,
        HandlebarsPlannerOptions? plannerOptions = null,
        KernelArguments? initialContext = null,
        bool shouldPrintPrompt = false,
        bool shouldInvokePlan = true,
        params string[] pluginDirectoryNames)
    {
        var kernel = await SetupKernelAsync(pluginDirectoryNames);
        if (kernel is null)
        {
            return;
        }

        // Set the planner options
        plannerOptions ??= new HandlebarsPlannerOptions()
        {
            // When using OpenAI models, we recommend using low values for temperature and top_p to minimize planner hallucinations.
            ExecutionSettings = new OpenAIPromptExecutionSettings()
            {
                Temperature = 0.0,
                TopP = 0.1,
            },
        };

        // Use gpt-4 or newer models if you want to test with loops.
        // Older models like gpt-35-turbo are less recommended. They do handle loops but are more prone to syntax errors.
        plannerOptions.AllowLoops = TestConfiguration.AzureOpenAI.ChatDeploymentName.Contains("gpt-4", StringComparison.OrdinalIgnoreCase);

        // Instantiate the planner and create the plan
        var planner = new HandlebarsPlanner(plannerOptions);
        var plan = await planner.CreatePlanAsync(kernel, goal, initialContext);

        // Execute the plan
        var result = shouldInvokePlan ? await plan.InvokeAsync(kernel, initialContext) : string.Empty;

        PrintPlannerDetails(goal, plan, result, shouldPrintPrompt);
    }

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(false)]
    public async Task PlanNotPossibleSampleAsync(bool shouldPrintPrompt)
    {
        try
        {
            WriteSampleHeading("Plan Not Possible");

            // Load additional plugins to enable planner but not enough for the given goal.
            await RunSampleAsync("Send Mary an email with the list of meetings I have scheduled today.", null, null, shouldPrintPrompt, true, "SummarizePlugin");
            /*
                [InsufficientFunctionsForGoal] Unable to create plan for goal with available functions.
                Goal: Send Mary an email with the list of meetings I have scheduled today.
                Available Functions: SummarizePlugin-MakeAbstractReadable, SummarizePlugin-Notegen, SummarizePlugin-Summarize, SummarizePlugin-Topics
                Planner output:
                As the available helpers do not contain any functionality to send an email or interact with meeting scheduling data, I cannot create a template to achieve the stated goal. 
                Additional helpers or information may be required.
            */
        }
        catch (Exception e)
        {
            Console.WriteLine(e.InnerException?.Message);
        }
    }

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(true)]

    public Task RunCourseraSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("Coursera OpenAPI Plugin");
        return RunSampleAsync("Show me courses about Artificial Intelligence.", null, null, shouldPrintPrompt, true, CourseraPluginName);
        /*
            Original plan:
            {{!-- Step 0: Extract key values --}}
            {{set "query" "Artificial Intelligence"}}

            {{!-- Step 1: Call CourseraPlugin-search with the query --}}
            {{set "searchResults" (CourseraPlugin-search query=query)}}

            {{!-- Step 2: Loop through the search results and display course information --}}
            {{#each searchResults.hits}}
                {{json (concat "Course Name: " this.name ", URL: " this.objectUrl)}}
            {{/each}}

            Result:
            Course Name: Introduction to Artificial Intelligence (AI), URL: https://www.coursera.org/learn/introduction-to-ai?utm_source=rest_api
            Course Name: IBM Applied AI, URL: https://www.coursera.org/professional-certificates/applied-artifical-intelligence-ibm-watson-ai?utm_source=rest_api
            Course Name: AI For Everyone, URL: https://www.coursera.org/learn/ai-for-everyone?utm_source=rest_api
            Course Name: Python for Data Science, AI & Development, URL: https://www.coursera.org/learn/python-for-applied-data-science-ai?utm_source=rest_api
            Course Name: Introduction to Generative AI, URL: https://www.coursera.org/learn/introduction-to-generative-ai?utm_source=rest_api
            Course Name: Deep Learning, URL: https://www.coursera.org/specializations/deep-learning?utm_source=rest_api
            Course Name: Machine Learning, URL: https://www.coursera.org/specializations/machine-learning-introduction?utm_source=rest_api
            Course Name: IBM AI Engineering, URL: https://www.coursera.org/professional-certificates/ai-engineer?utm_source=rest_api

        */
    }

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(false)]
    public Task RunDictionaryWithBasicTypesSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("Basic Types using Local Dictionary Plugin");
        return RunSampleAsync("Get a random word and its definition.", null, null, shouldPrintPrompt, true, StringParamsDictionaryPlugin.PluginName);
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

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(true)]
    public Task RunLocalDictionaryWithComplexTypesSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("Complex Types using Local Dictionary Plugin");
        return RunSampleAsync("Teach me two random words and their definition.", null, null, shouldPrintPrompt, true, ComplexParamsDictionaryPlugin.PluginName);
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

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(false)]
    public Task RunPoetrySampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("Multiple Plugins");
        return RunSampleAsync("Write a poem about John Doe, then translate it into Italian.", null, null, shouldPrintPrompt, true, "SummarizePlugin", "WriterPlugin");
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

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(false)]
    public Task RunBookSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("Loops and Conditionals");
        return RunSampleAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'", null, null, shouldPrintPrompt, true, "WriterPlugin", "MiscPlugin");
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

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(true)]
    public Task RunPredefinedVariablesSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("CreatePlan Prompt With Predefined Variables");

        // When using predefined variables, you must pass these arguments to both the CreatePlanAsync and InvokeAsync methods.
        var initialArguments = new KernelArguments()
        {
            { "greetings", new List<string>(){ "hey", "bye" } },
            { "someNumber", 1 },
            { "person", new Dictionary<string, string>()
            {
                {"name", "John Doe" },
                { "language", "Italian" },
            } }
        };

        return RunSampleAsync("Write a poem about the given person, then translate it into French.", null, initialArguments, shouldPrintPrompt, true, "WriterPlugin", "MiscPlugin");
        /*
            Original plan:
            {{!-- Step 0: Extract key values --}}
            {{set "personName" @root.person.name}}

            {{!-- Step 1: Generate a short poem about the person --}}
            {{set "poem" (WriterPlugin-ShortPoem input=personName)}}

            {{!-- Step 2: Translate the poem into French --}}
            {{set "translatedPoem" (WriterPlugin-Translate input=poem language="French")}}

            {{!-- Step 3: Output the translated poem --}}
            {{json translatedPoem}}

            Result:
            Il était une fois un gars nommé Doe,
            Dont la vie était un spectacle comique,
            Il trébuchait et tombait,
            Mais riait à travers tout cela,
            Alors qu'il dansait dans la vie, de-ci de-là.
        */
    }

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(true)]
    public Task RunPromptWithAdditionalContextSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("Prompt With Additional Context");

        // Pulling the raw content from SK's README file as domain context.
        static async Task<string> getDomainContext()
        {
            // For demonstration purposes only, beware of token count.
            var repositoryUrl = "https://github.com/microsoft/semantic-kernel";
            var readmeUrl = $"{repositoryUrl}/main/README.md".Replace("github.com", "raw.githubusercontent.com", StringComparison.CurrentCultureIgnoreCase);
            try
            {
                var httpClient = new HttpClient();
                // Send a GET request to the specified URL  
                var response = await httpClient.GetAsync(new Uri(readmeUrl));
                response.EnsureSuccessStatusCode(); // Throw an exception if not successful  

                // Read the response content as a string  
                var content = await response.Content.ReadAsStringAsync();
                httpClient.Dispose();
                return "Content imported from the README of https://github.com/microsoft/semantic-kernel:\n" + content;
            }
            catch (HttpRequestException e)
            {
                System.Console.WriteLine("\nException Caught!");
                System.Console.WriteLine("Message :{0} ", e.Message);
                return "";
            }
        }

        var goal = "Help me onboard to the Semantic Kernel SDK by creating a quick guide that includes a brief overview of the SDK for C# developers and detailed set-up steps. Include relevant links where possible. Then, draft an email with this guide, so I can share it with my team.";
        var plannerOptions = new HandlebarsPlannerOptions()
        {
            // Context to be used in the prompt template.
            GetAdditionalPromptContext = getDomainContext,
        };

        return RunSampleAsync(goal, plannerOptions, null, shouldPrintPrompt, true, "WriterPlugin");
        /*
            {{!-- Step 0: Extract Key Values --}}
            {{set "sdkLink" "https://learn.microsoft.com/en-us/semantic-kernel/overview/"}}
            {{set "nugetPackageLink" "https://www.nuget.org/packages/Microsoft.SemanticKernel/"}}
            {{set "csharpGetStartedLink" "dotnet/README.md"}}
            {{set "emailSubject" "Semantic Kernel SDK: Quick Guide for C# Developers"}}

            {{!-- Step 1: Create a concise guide and store it in a variable --}}
            {{set "guide" (concat "The Semantic Kernel SDK provides seamless integration between large language models (LLMs) and programming languages such as C#. " "To get started with the C# SDK, please follow these steps:\n\n" "1. Read the SDK Overview for a brief introduction here: " sdkLink "\n" "2. Install the Nuget package in your project: " nugetPackageLink "\n" "3. Follow the detailed set-up steps in the C# 'Getting Started' guide: " csharpGetStartedLink "\n\n" "Feel free to share this quick guide with your team members to help them onboard quickly with the Semantic Kernel SDK. ")}}

            {{!-- Step 2: Generate a draft email with the guide --}}
            {{set "emailBody" (concat "Hi Team,\n\n" "I have put together a quick guide to help you onboard to the Semantic Kernel SDK for C# developers. " "This guide includes a brief overview and detailed set-up steps:\n\n" guide "\n\n" "I have attached a more comprehensive guide as a document. Please review it and let me know if you have any questions. " "Let's start integrating the Semantic Kernel SDK into our projects!\n\n" "Best Regards,\n" "Your Name ")}}

            {{json (concat "Subject: " emailSubject "\n\nBody:\n" emailBody)}}

            Result:
            Subject: Semantic Kernel SDK: Quick Guide for C# Developers
            
            Body:
            Hi Team,
            I have put together a quick guide to help you onboard to the Semantic Kernel SDK for C# developers. This guide includes a brief overview and detailed set-up steps:

            The Semantic Kernel SDK provides seamless integration between large language models (LLMs) and programming languages such as C#. To get started with the C# SDK, please follow these steps:
            1. Read the SDK Overview for a brief introduction here: https://learn.microsoft.com/en-us/semantic-kernel/overview/
            2. Install the Nuget package in your project: https://www.nuget.org/packages/Microsoft.SemanticKernel/
            3. Follow the detailed set-up steps in the C# 'Getting Started' guide: dotnet/README.md
            
            Feel free to share this quick guide with your team members to help them onboard quickly with the Semantic Kernel SDK.
            
            I have attached a more comprehensive guide as a document. Please review it and let me know if you have any questions. Let's start integrating the Semantic Kernel SDK into our projects!
            
            Best Regards,
            Your Name
        */
    }

    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(true)]
    public Task RunOverrideCreatePlanPromptSampleAsync(bool shouldPrintPrompt)
    {
        WriteSampleHeading("CreatePlan Prompt Override");

        static string OverridePlanPrompt()
        {
            // Load a custom CreatePlan prompt template from an embedded resource.
            var ResourceFileName = "65-prompt-override.handlebars";
            var fileContent = EmbeddedResource.ReadStream(ResourceFileName);
            return new StreamReader(fileContent!).ReadToEnd();
        }

        var plannerOptions = new HandlebarsPlannerOptions()
        {
            // Callback to override the default prompt template.
            CreatePlanPromptHandler = OverridePlanPrompt,
        };

        var goal = "I just watched the movie 'Inception' and I loved it! I want to leave a 5 star review. Can you help me?";

        // Note that since the custom prompt inputs a unique Helpers section with helpers not actually registered with the kernel,
        // any plan created using this prompt will fail execution; thus, we will skip the InvokePlan call in this example.
        // For a simpler example, see `ItOverridesPromptAsync` in the dotnet\src\Planners\Planners.Handlebars.UnitTests\Handlebars\HandlebarsPlannerTests.cs file.
        return RunSampleAsync(goal, plannerOptions, null, shouldPrintPrompt, shouldInvokePlan: false, "WriterPlugin");
    }
}
