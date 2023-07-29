// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Core;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example15_MemorySkill
{
    private const string MemoryCollectionName = "aboutMe";

    public static async Task RunAsync()
    {
        var kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Logger)
            .WithOpenAITextCompletionService("text-davinci-003", TestConfiguration.OpenAI.ApiKey)
            .WithOpenAITextEmbeddingGenerationService("text-embedding-ada-002", TestConfiguration.OpenAI.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        // ========= Store memories using the kernel =========

        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info1", text: "My name is Andrea");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info2", text: "I work as a tourist operator");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info3", text: "I've been living in Seattle since 2005");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info4", text: "I visited France and Italy five times since 2015");

        // ========= Store memories using semantic function =========

        // Add Memory as a skill for other functions
        var memorySkill = new TextMemorySkill(kernel.Memory);
        kernel.ImportSkill(memorySkill);

        // Build a semantic function that saves info to memory
        const string SaveFunctionDefinition = "{{save $info}}";
        var memorySaver = kernel.CreateSemanticFunction(SaveFunctionDefinition);

        await kernel.RunAsync(memorySaver, new()
        {
            [TextMemorySkill.CollectionParam] = MemoryCollectionName,
            [TextMemorySkill.KeyParam] = "info5",
            ["info"] = "My family is from New York"
        });

        // ========= Test memory remember =========
        Console.WriteLine("========= Example: Recalling a Memory =========");

        var answer = await memorySkill.RetrieveAsync(MemoryCollectionName, "info5", logger: kernel.Logger);
        Console.WriteLine("Memory associated with 'info1': {0}", answer);
        /*
        Output:
        "Memory associated with 'info1': My name is Andrea
        */

        // ========= Test memory recall =========
        Console.WriteLine("========= Example: Recalling an Idea =========");

        answer = await memorySkill.RecallAsync("where did I grow up?", MemoryCollectionName, relevance: null, limit: 2, logger: kernel.Logger);
        Console.WriteLine("Ask: where did I grow up?");
        Console.WriteLine("Answer:\n{0}", answer);

        answer = await memorySkill.RecallAsync("where do I live?", MemoryCollectionName, relevance: null, limit: 2, logger: kernel.Logger);
        Console.WriteLine("Ask: where do I live?");
        Console.WriteLine("Answer:\n{0}", answer);

        /*
        Output:

            Ask: where did I grow up?
            Answer:
                ["My family is from New York","I\u0027ve been living in Seattle since 2005"]

            Ask: where do I live?
            Answer:
                ["I\u0027ve been living in Seattle since 2005","My family is from New York"]
        */

        // ========= Use memory in a semantic function =========
        Console.WriteLine("========= Example: Using Recall in a Semantic Function =========");

        // Build a semantic function that uses memory to find facts
        const string RecallFunctionDefinition = @"
Consider only the facts below when answering questions.

About me: {{recall 'where did I grow up?'}}
About me: {{recall 'where do I live?'}}

Question: {{$input}}

Answer:
";

        var aboutMeOracle = kernel.CreateSemanticFunction(RecallFunctionDefinition, maxTokens: 100);

        var result = await kernel.RunAsync(aboutMeOracle, new("Do I live in the same town where I grew up?")
        {
            [TextMemorySkill.CollectionParam] = MemoryCollectionName,
            [TextMemorySkill.RelevanceParam] = "0.8"
        });

        Console.WriteLine("Do I live in the same town where I grew up?\n");
        Console.WriteLine(result);

        /*
        Output:

            Do I live in the same town where I grew up?

            No, I do not live in the same town where I grew up since my family is from New York and I have been living in Seattle since 2005.
        */

        // ========= Remove a memory =========
        Console.WriteLine("========= Example: Forgetting a Memory =========");

        result = await kernel.RunAsync(aboutMeOracle, new("Tell me a bit about myself")
        {
            ["fact1"] = "What is my name?",
            ["fact2"] = "What do I do for a living?",
            [TextMemorySkill.RelevanceParam] = ".75"
        });

        Console.WriteLine("Tell me a bit about myself\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            My name is Andrea and my family is from New York. I work as a tourist operator.
        */

        await memorySkill.RemoveAsync(MemoryCollectionName, "info1", logger: kernel.Logger);

        result = await kernel.RunAsync(aboutMeOracle, "Tell me a bit about myself");

        Console.WriteLine("Tell me a bit about myself\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            I'm from a family originally from New York and I work as a tourist operator. I've been living in Seattle since 2005.
        */
    }
}
