// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example15_MemorySkill
{
    private const string MemoryCollectionName = "aboutMe";

    public static async Task RunAsync()
    {
        var kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Log)
            .Configure(c =>
            {
                c.AddOpenAICompletionBackend("davinci", "text-davinci-003", Env.Var("OPENAI_API_KEY"));
                c.AddOpenAIEmbeddingsBackend("ada", "text-embedding-ada-002", Env.Var("OPENAI_API_KEY"));
            })
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        // ========= Store memories using the kernel =========

        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info1", text: "My name is Andrea");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info2", text: "I work as a tourist operator");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info3", text: "I've been living in Seattle since 2005");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "info4", text: "I visited France and Italy five times since 2015");

        // ========= Store memories using semantic function =========

        // Add Memory as a skill for other functions
        kernel.ImportSkill(new TextMemorySkill());

        // Build a semantic function that saves info to memory
        const string SAVE_FUNCTION_DEFINITION = @"{{save $info}}";
        var memorySaver = kernel.CreateSemanticFunction(SAVE_FUNCTION_DEFINITION);

        var context = kernel.CreateNewContext();
        context[TextMemorySkill.CollectionParam] = MemoryCollectionName;
        context[TextMemorySkill.KeyParam] = "info5";
        context["info"] = "My family is from New York";
        await memorySaver.InvokeAsync(context);

        // ========= Test memory =========

        await AnswerAsync("where did I grow up?", kernel);
        await AnswerAsync("where do I live?", kernel);

        /*
        Output:

            Ask: where did I grow up?
              Fact 1: My family is from New York (relevance: 0.8202760217073308)
              Fact 2: I've been living in Seattle since 2005 (relevance: 0.7923238361094278)

            Ask: where do I live?
              Fact 1: I've been living in Seattle since 2005 (relevance: 0.8010884368220728)
              Fact 2: My family is from New York (relevance: 0.785718105747128)
        */

        // ========= Use memory in a semantic function =========

        // Build a semantic function that uses memory to find facts
        const string RECALL_FUNCTION_DEFINITION = @"
Consider only the facts below when answering questions.

About me: {{recall $fact1}}
About me: {{recall $fact2}}

Question: {{$query}}

Answer:
";

        var aboutMeOracle = kernel.CreateSemanticFunction(RECALL_FUNCTION_DEFINITION, maxTokens: 100);

        context["fact1"] = "where did I grow up?";
        context["fact2"] = "where do I live?";
        context["query"] = "Do I live in the same town where I grew up?";
        context[TextMemorySkill.RelevanceParam] = "0.8";

        var result = await aboutMeOracle.InvokeAsync(context);

        Console.WriteLine(context["query"] + "\n");
        Console.WriteLine(result);

        /*
        Output:

            Do I live in the same town where I grew up?

            No, I do not live in the same town where I grew up since my family is from New York and I have been living in Seattle since 2005.
        */
    }

    private static async Task AnswerAsync(string ask, IKernel kernel)
    {
        Console.WriteLine($"Ask: {ask}");
        var memories = kernel.Memory.SearchAsync(MemoryCollectionName, ask, limit: 2, minRelevanceScore: 0.6);
        var i = 0;
        await foreach (MemoryQueryResult memory in memories)
        {
            Console.WriteLine($"  Fact {++i}: {memory.Text} (relevance: {memory.Relevance})");
        }

        Console.WriteLine();
    }
}
