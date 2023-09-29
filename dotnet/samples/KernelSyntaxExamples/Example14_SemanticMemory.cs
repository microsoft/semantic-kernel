// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;
using Microsoft.SemanticKernel.Memory;
using Reliability;
using RepoUtils;
using Resources;

/* The files contains two examples about SK Semantic Memory.
 *
 * 1. Memory using Azure Cognitive Search.
 * 2. Memory using a custom embedding generator and vector engine.
 *
 * Semantic Memory allows to store your data like traditional DBs,
 * adding the ability to query it using natural language.
 */

// ReSharper disable once InconsistentNaming
public static class Example14_SemanticMemory
{
    private const string MemoryCollectionName = "SKGitHub";

    public static async Task RunAsync()
    {
        await TryRun(RunACSExampleAsync);
        await TryRun(RunVolatileExampleAsync);
        await TryRun(RunLocalExampleAsync);
        await TryRun(RunLocalCustomExampleAsync);
    }

    public static async Task TryRun(Func<Task> task)
    {
        try
        {
            await task();
        }
        catch (ConfigurationNotFoundException ex)
        {
            Console.WriteLine($"{ex.Message}. Skipping example {task.Method}.");
        }
    }

    public static async Task RunACSExampleAsync()
    {
        Console.WriteLine("==============================================================");
        Console.WriteLine("======== Semantic Memory using Azure Cognitive Search ========");
        Console.WriteLine("==============================================================");

        /* This example leverages Azure Cognitive Search to provide SK with Semantic Memory.
         *
         * Azure Cognitive Search automatically indexes your data semantically, so you don't
         * need to worry about embedding generation.
         */

        var kernelWithACS = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAITextEmbeddingGenerationService("text-embedding-ada-002", TestConfiguration.OpenAI.ApiKey)
            .WithMemoryStorage(new AzureCognitiveSearchMemoryStore(TestConfiguration.ACS.Endpoint, TestConfiguration.ACS.ApiKey))
            .Build();

        await RunExampleAsync(kernelWithACS);
    }

    public static async Task RunVolatileExampleAsync()
    {
        Console.WriteLine("====================================================");
        Console.WriteLine("======== Semantic Memory (volatile, in RAM) ========");
        Console.WriteLine("====================================================");

        /* You can build your own semantic memory combining an Embedding Generator
         * with a Memory storage that supports search by similarity (ie semantic search).
         *
         * In this example we use a volatile memory, a local simulation of a vector DB.
         *
         * You can replace VolatileMemoryStore with Qdrant (see QdrantMemoryStore connector)
         * or implement your connectors for Pinecone, Vespa, Postgres + pgvector, SQLite VSS, etc.
         */

        var kernelWithCustomDb = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAITextEmbeddingGenerationService("ada", "text-embedding-ada-002", TestConfiguration.OpenAI.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        await RunExampleAsync(kernelWithCustomDb);
    }

    public static async Task RunLocalExampleAsync()
    {
        Console.WriteLine("====================================================");
        Console.WriteLine("======== Semantic Memory (local embeddings) ========");
        Console.WriteLine("====================================================");

        /* You can also use a local embedding generator.
         *
         * In this example we use a local embedding generator that uses a local
         * embedding generator based on Microsoft.ML tokenizers.
         */

        var kernelWithLocalEmbeddings = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithMicrosoftMLTextEmbeddingGenerationService(serviceId: "roberta", setAsDefault: true) // TODO Files are missing
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        await RunExampleAsync(kernelWithLocalEmbeddings);
    }

    public static async Task RunLocalCustomExampleAsync()
    {
        Console.WriteLine("====================================================");
        Console.WriteLine("======== Semantic Memory (local custom embeddings) ========");
        Console.WriteLine("====================================================");

        /* You can also use a local embedding generator.
         *
         * In this example we use a local embedding generator that uses a local
         * embedding generator based on Microsoft.ML tokenizers.
         */

        var encoder = EmbeddedResource.ReadStream("EnglishRoberta.encoder.json");
        var vocab = EmbeddedResource.ReadStream("EnglishRoberta.vocab.bpe");
        var dict = EmbeddedResource.ReadStream("EnglishRoberta.dict.txt");

        if (encoder is null || vocab is null || dict is null)
        {
            throw new System.IO.FileNotFoundException("Missing required resources");
        }

        Microsoft.ML.Tokenizers.EnglishRoberta model = new(encoder, vocab, dict);

        Microsoft.ML.Tokenizers.Tokenizer tokenizer = new(model, new Microsoft.ML.Tokenizers.RobertaPreTokenizer());

        var kernelWithLocalEmbeddings = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithMicrosoftMLTextEmbeddingGenerationService(tokenizer: tokenizer, serviceId: "roberta", setAsDefault: true) // TODO Array lengths must be equal
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        await RunExampleAsync(kernelWithLocalEmbeddings);
    }

    public static async Task RunExampleAsync(IKernel kernel)
    {
        await StoreMemoryAsync(kernel);

        await SearchMemoryAsync(kernel, "How do I get started?");

        /*
        Output:

        Query: How do I get started?

        Result 1:
          URL:     : https://github.com/microsoft/semantic-kernel/blob/main/README.md
          Title    : README: Installation, getting started, and how to contribute

        Result 2:
          URL:     : https://github.com/microsoft/semantic-kernel/blob/main/samples/dotnet-jupyter-notebooks/00-getting-started.ipynb
          Title    : Jupyter notebook describing how to get started with the Semantic Kernel

        */

        await SearchMemoryAsync(kernel, "Can I build a chat with SK?");

        /*
        Output:

        Query: Can I build a chat with SK?

        Result 1:
          URL:     : https://github.com/microsoft/semantic-kernel/tree/main/samples/plugins/ChatPlugin/ChatGPT
          Title    : Sample demonstrating how to create a chat plugin interfacing with ChatGPT

        Result 2:
          URL:     : https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/chat-summary-webapp-react/README.md
          Title    : README: README associated with a sample chat summary react-based webapp

        */
    }

    private static async Task SearchMemoryAsync(IKernel kernel, string query)
    {
        Console.WriteLine("\nQuery: " + query + "\n");

        var memories = kernel.Memory.SearchAsync(MemoryCollectionName, query, limit: 2, minRelevanceScore: 0.5);

        int i = 0;
        await foreach (MemoryQueryResult memory in memories)
        {
            Console.WriteLine($"Result {++i}:");
            Console.WriteLine("  URL:     : " + memory.Metadata.Id);
            Console.WriteLine("  Title    : " + memory.Metadata.Description);
            Console.WriteLine("  Relevance: " + memory.Relevance);
            Console.WriteLine();
        }

        Console.WriteLine("----------------------");
    }

    private static async Task StoreMemoryAsync(IKernel kernel)
    {
        /* Store some data in the semantic memory.
         *
         * When using Azure Cognitive Search the data is automatically indexed on write.
         *
         * When using the combination of VolatileStore and Embedding generation, SK takes
         * care of creating and storing the index
         */

        Console.WriteLine("\nAdding some GitHub file URLs and their descriptions to the semantic memory.");
        var githubFiles = SampleData();
        var i = 0;
        foreach (var entry in githubFiles)
        {
            await kernel.Memory.SaveReferenceAsync(
                collection: MemoryCollectionName,
                externalSourceName: "GitHub",
                externalId: entry.Key,
                description: entry.Value,
                text: entry.Value);

            Console.Write($" #{++i} saved.");
        }

        Console.WriteLine("\n----------------------");
    }

    private static Dictionary<string, string> SampleData()
    {
        return new Dictionary<string, string>
        {
            ["https://github.com/microsoft/semantic-kernel/blob/main/README.md"]
                = "README: Installation, getting started, and how to contribute",
            ["https://github.com/microsoft/semantic-kernel/blob/main/dotnet/notebooks/02-running-prompts-from-file.ipynb"]
                = "Jupyter notebook describing how to pass prompts from a file to a semantic plugin or function",
            ["https://github.com/microsoft/semantic-kernel/blob/main/dotnet/notebooks//00-getting-started.ipynb"]
                = "Jupyter notebook describing how to get started with the Semantic Kernel",
            ["https://github.com/microsoft/semantic-kernel/tree/main/samples/plugins/ChatPlugin/ChatGPT"]
                = "Sample demonstrating how to create a chat plugin interfacing with ChatGPT",
            ["https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel/Memory/VolatileMemoryStore.cs"]
                = "C# class that defines a volatile embedding store",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/dotnet/KernelHttpServer/README.md"]
                = "README: How to set up a Semantic Kernel Service API using Azure Function Runtime v4",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/chat-summary-webapp-react/README.md"]
                = "README: README associated with a sample chat summary react-based webapp",
        };
    }
}
