// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Core;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example15_MemorySkill
{
    private const string MemorySkillName = "memory";
    private const string MemoryCollectionName = "aboutMe";

    public static async Task RunAsync()
    {
        var kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Log)
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
        kernel.ImportSkill(new TextMemorySkill(kernel.Memory), MemorySkillName);

        // Build a semantic function that saves info to memory
        const string SaveFunctionDefinition = "{{save $info}}";
        var memorySaver = kernel.CreateSemanticFunction(SaveFunctionDefinition);

        var result = await kernel.RunAsync(memorySaver,
            input: "Do I live in the same town where I grew up?",
            args: new Dictionary<string, string>
            {
                [TextMemorySkill.CollectionParam] = MemoryCollectionName,
                [TextMemorySkill.KeyParam] = "info5",
                ["info"] = "My family is from New York"
            });

        // ========= Test memory remember =========
        Console.WriteLine("========= Example: Retrieving a memory by key =========");

        var answer = await kernel.RunAsync(MemorySkillName, "Retrieve",
            args: new Dictionary<string, string>
            {
                [TextMemorySkill.CollectionParam] = MemoryCollectionName,
                [TextMemorySkill.KeyParam] = "info5"
            });

        Console.WriteLine("Memory associated with 'info1': {0}", answer);
        /*
        Output:
        "Memory associated with 'info1': My name is Andrea
        */

        // ========= Test memory recall =========
        Console.WriteLine("========= Example: Recalling an idea by relevance =========");

        answer = await kernel.RunAsync(MemorySkillName, "Recall",
            input: "where did I grow up?",
            args: new Dictionary<string, string>
            {
                [TextMemorySkill.CollectionParam] = MemoryCollectionName,
                [TextMemorySkill.LimitParam] = "2"
            });

        Console.WriteLine("Ask: where did I grow up?");
        Console.WriteLine("Answer:\n{0}", answer);

        answer = await kernel.RunAsync(MemorySkillName, "Recall",
            input: "where do I live?",
            args: new Dictionary<string, string>
            {
                [TextMemorySkill.CollectionParam] = MemoryCollectionName,
                [TextMemorySkill.LimitParam] = "2"
            });

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
        result = await kernel.RunAsync(aboutMeOracle,
            input: "Do I live in the same town where I grew up?",
            args: new Dictionary<string, string>
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

        result = await kernel.RunAsync(aboutMeOracle,
            input: "Tell me a bit about myself",
            args: new Dictionary<string, string>
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

        // Remove memory with key "info1"
        await kernel.RunAsync(skillName: MemorySkillName, functionName: "Remove",
            args: new Dictionary<string, string>
            {
                [TextMemorySkill.CollectionParam] = MemoryCollectionName,
                [TextMemorySkill.KeyParam] = "info1"
            });

        result = await kernel.RunAsync(aboutMeOracle,
            input: "Tell me a bit about myself",
            args: new Dictionary<string, string>
            {
                [TextMemorySkill.KeyParam] = "info1"
            });

        Console.WriteLine("Tell me a bit about myself\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            I'm from a family originally from New York and I work as a tourist operator. I've been living in Seattle since 2005.
        */
    }
}
