// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
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
                c.AddOpenAITextCompletionService("text-davinci-003", Env.Var("OPENAI_API_KEY"));
                c.AddOpenAITextEmbeddingGenerationService("text-embedding-ada-002", Env.Var("OPENAI_API_KEY"));
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
        var memorySkill = new TextMemorySkill();
        kernel.ImportSkill(new TextMemorySkill());

        // Build a semantic function that saves info to memory
        const string SaveFunctionDefinition = @"{{save $info}}";
        var memorySaver = kernel.CreateSemanticFunction(SaveFunctionDefinition);

        var context = kernel.CreateNewContext();
        context[TextMemorySkill.CollectionParam] = MemoryCollectionName;
        context[TextMemorySkill.KeyParam] = "info5";
        context["info"] = "My family is from New York";
        await memorySaver.InvokeAsync(context);

        // ========= Test memory remember =========
        Console.WriteLine("========= Example: Recalling a Memory =========");

        context[TextMemorySkill.KeyParam] = "info1";
        var answer = await memorySkill.RetrieveAsync(context);
        Console.WriteLine("Memory associated with 'info1': {0}", answer);
        /*
        Output:
        "Memory associated with 'info1': My name is Andrea
        */

        // ========= Test memory recall =========
        Console.WriteLine("========= Example: Recalling an Idea =========");

        context[TextMemorySkill.LimitParam] = "2";
        string ask = "where did I grow up?";
        answer = await memorySkill.RecallAsync(ask, context);
        Console.WriteLine("Ask: {0}", ask);
        Console.WriteLine("Answer:\n{0}", answer);

        ask = "where do I live?";
        answer = await memorySkill.RecallAsync(ask, context);
        Console.WriteLine("Ask: {0}", ask);
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

Question: {{$query}}

Answer:
";

        var aboutMeOracle = kernel.CreateSemanticFunction(RecallFunctionDefinition, maxTokens: 100);

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

        // ========= Remove a memory =========
        Console.WriteLine("========= Example: Forgetting a Memory =========");

        context["fact1"] = "What is my name?";
        context["fact2"] = "What do I do for a living?";
        context["query"] = "Tell me a bit about myself";
        context[TextMemorySkill.RelevanceParam] = ".75";

        result = await aboutMeOracle.InvokeAsync(context);

        Console.WriteLine(context["query"] + "\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            My name is Andrea and my family is from New York. I work as a tourist operator.
        */

        context[TextMemorySkill.KeyParam] = "info1";
        await memorySkill.RemoveAsync(context);

        result = await aboutMeOracle.InvokeAsync(context);

        Console.WriteLine(context["query"] + "\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            I'm from a family originally from New York and I work as a tourist operator. I've been living in Seattle since 2005.
        */
    }
}
