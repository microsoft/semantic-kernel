// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example14_Memory
{
    public static async Task RunAsync()
    {
        const string memoryCollectionName = "SKGitHub";

        var githubFiles = new Dictionary<string, string>()
        {
            ["https://github.com/microsoft/semantic-kernel/blob/main/README.md"]
                = "README: Installation, getting started, and how to contribute",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/notebooks/dotnet/02-running-prompts-from-file.ipynb"]
                = "Jupyter notebook describing how to pass prompts from a file to a semantic skill or function",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/notebooks/dotnet/00-getting-started.ipynb"]
                = "Jupyter notebook describing how to get started with the Semantic Kernel",
            ["https://github.com/microsoft/semantic-kernel/tree/main/samples/skills/ChatSkill/ChatGPT"]
                = "Sample demonstrating how to create a chat skill interfacing with ChatGPT",
            ["https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel/Memory/VolatileMemoryStore.cs"]
                = "C# class that defines a volatile embedding store",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/dotnet/KernelHttpServer/README.md"]
                = "README: How to set up a Semantic Kernel Service API using Azure Function Runtime v4",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/chat-summary-webapp-react/README.md"]
                = "README: README associated with a sample chat summary react-based webapp",
        };

        var kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Log)
            .Configure(c => c.AddOpenAITextEmbeddingGenerationService("ada", "text-embedding-ada-002", Env.Var("OPENAI_API_KEY")))
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        // ========= Store memories =========

        Console.WriteLine("Adding some GitHub file URLs and their descriptions to a volatile Semantic Memory.");
        var i = 0;
        foreach (var entry in githubFiles)
        {
            await kernel.Memory.SaveReferenceAsync(
                collection: memoryCollectionName,
                description: entry.Value,
                text: entry.Value,
                externalId: entry.Key,
                externalSourceName: "GitHub"
            );
            Console.WriteLine($"  URL {++i} saved");
        }

        Console.WriteLine("Files added.");

        /*
        Output:

        Adding some GitHub file URLs and their descriptions to a volatile Semantic Memory.
          URL 1 saved
          URL 2 saved
          URL 3 saved
          URL 4 saved
          URL 5 saved
          URL 6 saved
          URL 7 saved
        Files added.
        */

        // ========= Search semantic memory #1 =========

        string ask = "How do I get started?";
        Console.WriteLine("===========================\n" +
                          "Query: " + ask + "\n");

        var memories = kernel.Memory.SearchAsync(memoryCollectionName, ask, limit: 5, minRelevanceScore: 0.77);

        i = 0;
        await foreach (MemoryQueryResult memory in memories)
        {
            Console.WriteLine($"Result {++i}:");
            Console.WriteLine("  URL:     : " + memory.Metadata.Id);
            Console.WriteLine("  Title    : " + memory.Metadata.Description);
            Console.WriteLine("  Relevance: " + memory.Relevance);
            Console.WriteLine();
        }

        /*
        Output:

        Query: How do I get started?

        Result 1:
          URL:     : https://github.com/microsoft/semantic-kernel/blob/main/README.md
          Title    : README: Installation, getting started, and how to contribute
          Relevance: 0.8233838875772925

        Result 2:
          URL:     : https://github.com/microsoft/semantic-kernel/blob/main/samples/dotnet-jupyter-notebooks/00-getting-started.ipynb
          Title    : Jupyter notebook describing how to get started with the Semantic Kernel
          Relevance: 0.7920580994199448

        */

        // ========= Search semantic memory #1 =========

        ask = "Can I build a chat with SK?";
        Console.WriteLine("===========================\n" +
                          "Query: " + ask + "\n");

        memories = kernel.Memory.SearchAsync(memoryCollectionName, ask, limit: 5, minRelevanceScore: 0.77);

        i = 0;
        await foreach (MemoryQueryResult memory in memories)
        {
            Console.WriteLine($"Result {++i}:");
            Console.WriteLine("  URL:     : " + memory.Metadata.Id);
            Console.WriteLine("  Title    : " + memory.Metadata.Description);
            Console.WriteLine("  Relevance: " + memory.Relevance);
            Console.WriteLine();
        }

        /*
        Output:

        Query: Can I build a chat with SK?

        Result 1:
          URL:     : https://github.com/microsoft/semantic-kernel/tree/main/samples/skills/ChatSkill/ChatGPT
          Title    : Sample demonstrating how to create a chat skill interfacing with ChatGPT
          Relevance: 0.8085974721867045
        */
    }
}
