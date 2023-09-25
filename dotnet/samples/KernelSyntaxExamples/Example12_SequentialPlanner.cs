// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planners;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Plugins;
using RepoUtils;

// ReSharper disable CommentTypo
// ReSharper disable once InconsistentNaming
internal static class Example12_SequentialPlanner
{
    public static async Task RunAsync()
    {
        await PoetrySamplesAsync();
        await EmailSamplesWithRecallAsync();
        await BookSamplesAsync();
        await MemorySampleAsync();
        await PlanNotPossibleSampleAsync();
    }

    private static async Task PlanNotPossibleSampleAsync()
    {
        Console.WriteLine("======== Sequential Planner - Plan Not Possible ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional plugins to enable planner but not enough for the given goal.
        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportSemanticFunctionsFromDirectory(folder, "SummarizePlugin");

        try
        {
            await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");
        }
        catch (SKException e)
        {
            Console.WriteLine(e.Message);
            // Create plan error: Not possible to create plan for goal with available functions.
            // Goal:Write a poem about John Doe, then translate it into Italian.
            // Functions:
            // SummarizePlugin.MakeAbstractReadable:
            //   description: Given a scientific white paper abstract, rewrite it to make it more readable
            //   inputs:
            //     - input:

            // SummarizePlugin.Notegen:
            //   description: Automatically generate compact notes for any text or text document.
            //   inputs:
            //     - input:

            // SummarizePlugin.Summarize:
            //   description: Summarize given text or any text document
            //   inputs:
            //     - input: Text to summarize

            // SummarizePlugin.Topics:
            //   description: Analyze given text or document and extract key topics worth remembering
            //   inputs:
            //     - input:
        }
    }

    private static async Task PoetrySamplesAsync()
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Poetry Plan ========");
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportSemanticFunctionsFromDirectory(folder,
           "SummarizePlugin",
           "WriterPlugin");

        var planner = new SequentialPlanner(kernel);

        var plan = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");

        // Original plan:
        // Goal: Write a poem about John Doe, then translate it into Italian.

        // Steps:
        // - WriterPlugin.ShortPoem INPUT='John Doe is a friendly guy who likes to help others and enjoys reading books.' =>
        // - WriterPlugin.Translate language='Italian' INPUT='' =>

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.GetValue<string>());
    }

    private static async Task EmailSamplesWithRecallAsync()
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Email Plan ========");
        var kernel = InitializeKernelAndPlanner(out var planner, 512);
        kernel.ImportFunctions(new EmailPlugin(), "email");

        // Load additional plugins to enable planner to do non-trivial asks.
        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportSemanticFunctionsFromDirectory(folder,
           "SummarizePlugin",
           "WriterPlugin");

        var plan = await planner.CreatePlanAsync("Summarize an input, translate to french, and e-mail to John Doe");

        // Original plan:
        // Goal: Summarize an input, translate to french, and e-mail to John Doe

        // Steps:
        // - SummarizePlugin.Summarize INPUT='' =>
        // - WriterPlugin.Translate language='French' INPUT='' => TRANSLATED_SUMMARY
        // - email.GetEmailAddress INPUT='John Doe' => EMAIL_ADDRESS
        // - email.SendEmail INPUT='$TRANSLATED_SUMMARY' email_address='$EMAIL_ADDRESS' =>

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());

        // Serialize plan before execution for saving to memory on success.
        var originalPlan = plan.ToJson();

        var input =
            "Once upon a time, in a faraway kingdom, there lived a kind and just king named Arjun. " +
            "He ruled over his kingdom with fairness and compassion, earning him the love and admiration of his people. " +
            "However, the kingdom was plagued by a terrible dragon that lived in the nearby mountains and terrorized the nearby villages, " +
            "burning their crops and homes. The king had tried everything to defeat the dragon, but to no avail. " +
            "One day, a young woman named Mira approached the king and offered to help defeat the dragon. She was a skilled archer " +
            "and claimed that she had a plan to defeat the dragon once and for all. The king was skeptical, but desperate for a solution, " +
            "so he agreed to let her try. Mira set out for the dragon's lair and, with the help of her trusty bow and arrow, " +
            "she was able to strike the dragon with a single shot through its heart, killing it instantly. The people rejoiced " +
            "and the kingdom was at peace once again. The king was so grateful to Mira that he asked her to marry him and she agreed. " +
            "They ruled the kingdom together, ruling with fairness and compassion, just as Arjun had done before. They lived " +
            "happily ever after, with the people of the kingdom remembering Mira as the brave young woman who saved them from the dragon.";
        await ExecutePlanAsync(kernel, plan, input, 5);

        Console.WriteLine("======== Sequential Planner - Find and Execute Saved Plan ========");

        // Save the plan for future use
        var semanticMemory = GetMemory();
        await semanticMemory.SaveInformationAsync(
            "plans",
            id: Guid.NewGuid().ToString(),
            text: plan.Description, // This is the goal used to create the plan
            description: originalPlan);

        var goal = "Write summary in french and e-mail John Doe";

        Console.WriteLine($"Goal: {goal}");
        Console.WriteLine("Searching for saved plan...");

        Plan? restoredPlan = null;
        var memories = semanticMemory.SearchAsync("plans", goal, limit: 1, minRelevanceScore: 0.5);
        await foreach (MemoryQueryResult memory in memories)
        {
            Console.WriteLine($"Restored plan (relevance={memory.Relevance}):");

            // Deseriliaze the plan from the description
            restoredPlan = Plan.FromJson(memory.Metadata.Description, kernel.Functions);

            Console.WriteLine(restoredPlan.ToPlanWithGoalString());
            Console.WriteLine();

            break;
        }

        if (restoredPlan is not null)
        {
            var newInput =
            "Far in the future, on a planet lightyears away, 15 year old Remy lives a normal life. He goes to school, " +
            "hangs out with his friends, and tries to avoid trouble. But when he stumbles across a secret that threatens to destroy " +
            "everything he knows, he's forced to go on the run. With the help of a mysterious girl named Eve, he must evade the ruthless " +
            "agents of the Galactic Federation, and uncover the truth about his past. But the more he learns, the more he realizes that " +
            "he's not just an ordinary boy.";

            var result = await kernel.RunAsync(restoredPlan, new(newInput));

            Console.WriteLine("Result:");
            Console.WriteLine(result.GetValue<string>());
        }
    }

    private static async Task BookSamplesAsync()
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Book Creation Plan  ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        // Load additional plugins to enable planner to do non-trivial asks.
        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportSemanticFunctionsFromDirectory(folder, "WriterPlugin");
        kernel.ImportSemanticFunctionsFromDirectory(folder, "MiscPlugin");

        var originalPlan = await planner.CreatePlanAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'");

        // Original plan:
        // Goal: Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'

        // Steps:
        // - WriterPlugin.NovelOutline chapterCount='3' INPUT='A group of kids in a club called 'The Thinking Caps' that solve mysteries and puzzles using their creativity and logic.' endMarker='<!--===ENDPART===-->' => OUTLINE
        // - MiscPlugin.ElementAtIndex count='3' INPUT='$OUTLINE' index='0' => CHAPTER_1_SYNOPSIS
        // - WriterPlugin.NovelChapter chapterIndex='1' previousChapter='' INPUT='$CHAPTER_1_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_1
        // - MiscPlugin.ElementAtIndex count='3' INPUT='$OUTLINE' index='1' => CHAPTER_2_SYNOPSIS
        // - WriterPlugin.NovelChapter chapterIndex='2' previousChapter='$CHAPTER_1_SYNOPSIS' INPUT='$CHAPTER_2_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_2
        // - MiscPlugin.ElementAtIndex count='3' INPUT='$OUTLINE' index='2' => CHAPTER_3_SYNOPSIS
        // - WriterPlugin.NovelChapter chapterIndex='3' previousChapter='$CHAPTER_2_SYNOPSIS' INPUT='$CHAPTER_3_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_3

        Console.WriteLine("Original plan:");
        Console.WriteLine(originalPlan.ToPlanWithGoalString());

        Stopwatch sw = new();
        sw.Start();
        await ExecutePlanAsync(kernel, originalPlan);
    }

    private static async Task MemorySampleAsync()
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Plan using Memory ========");

        var kernel = InitializeKernelWithMemory();

        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportSemanticFunctionsFromDirectory(folder,
           "SummarizePlugin",
           "WriterPlugin",
           "CalendarPlugin",
           "ChatPlugin",
           "ChildrensBookPlugin",
           "ClassificationPlugin",
           "CodingPlugin",
           "FunPlugin",
           "IntentDetectionPlugin",
           "MiscPlugin",
           "QAPlugin");

        kernel.ImportFunctions(new EmailPlugin(), "email");
        kernel.ImportFunctions(new StaticTextPlugin(), "statictext");
        kernel.ImportFunctions(new TextPlugin(), "coretext");

        var goal = "Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'";

        // IMPORTANT: To use memory and embeddings to find relevant plugins in the planner, set the 'Memory' property on the planner config.
        var planner = new SequentialPlanner(kernel, new SequentialPlannerConfig { RelevancyThreshold = 0.5, Memory = kernel.Memory });

        var plan = await planner.CreatePlanAsync(goal);

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());
    }

    private static IKernel InitializeKernelAndPlanner(out SequentialPlanner planner, int maxTokens = 1024)
    {
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        planner = new SequentialPlanner(kernel, new SequentialPlannerConfig { MaxTokens = maxTokens });

        return kernel;
    }

    private static IKernel InitializeKernelWithMemory()
    {
        // IMPORTANT: Register an embedding generation service and a memory store. The Planner will
        // use these to generate and store embeddings for the function descriptions.
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .WithAzureTextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                TestConfiguration.AzureOpenAIEmbeddings.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        return kernel;
    }

    private static ISemanticTextMemory GetMemory(IKernel? kernel = null)
    {
        if (kernel is not null)
        {
            return kernel.Memory;
        }
        var memoryStorage = new VolatileMemoryStore();
        var textEmbeddingGenerator = new Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding.AzureTextEmbeddingGeneration(
            modelId: TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            endpoint: TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            apiKey: TestConfiguration.AzureOpenAIEmbeddings.ApiKey);
        var memory = new SemanticTextMemory(memoryStorage, textEmbeddingGenerator);
        return memory;
    }

    private static async Task<Plan> ExecutePlanAsync(
        IKernel kernel,
        Plan plan,
        string input = "",
        int maxSteps = 10)
    {
        Stopwatch sw = new();
        sw.Start();

        // loop until complete or at most N steps
        try
        {
            for (int step = 1; plan.HasNextStep && step < maxSteps; step++)
            {
                if (string.IsNullOrEmpty(input))
                {
                    await plan.InvokeNextStepAsync(kernel.CreateNewContext());
                    // or await kernel.StepAsync(plan);
                }
                else
                {
                    plan = await kernel.StepAsync(input, plan);
                    input = string.Empty;
                }

                if (!plan.HasNextStep)
                {
                    Console.WriteLine($"Step {step} - COMPLETE!");
                    Console.WriteLine(plan.State.ToString());
                    break;
                }

                Console.WriteLine($"Step {step} - Results so far:");
                Console.WriteLine(plan.State.ToString());
            }
        }
        catch (SKException e)
        {
            Console.WriteLine("Step - Execution failed:");
            Console.WriteLine(e.Message);
        }

        sw.Stop();
        Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        return plan;
    }
}
