// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;
using Microsoft.SemanticKernel.Memory;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example50_Chroma
{
    private const string MemoryCollectionName = "chroma-test";

    public static async Task RunAsync()
    {
        string endpoint = TestConfiguration.Chroma.Endpoint;

        var memoryStore = new ChromaMemoryStore(endpoint);

        IKernel kernel = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .WithOpenAITextEmbeddingGenerationService(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .WithMemoryStorage(memoryStore)
            //.WithChromaMemoryStore(endpoint) // This method offers an alternative approach to registering Chroma memory store.
            .Build();

        Console.WriteLine("== Printing Collections in DB ==");
        var collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Adding Memories ==");

        var key1 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: Guid.NewGuid().ToString(), text: "british short hair");
        var key2 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: Guid.NewGuid().ToString(), text: "orange tabby");
        var key3 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: Guid.NewGuid().ToString(), text: "norwegian forest cat");

        Console.WriteLine("== Printing Collections in DB ==");
        collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Retrieving Memories Through the Kernel ==");
        MemoryQueryResult? lookup = await kernel.Memory.GetAsync(MemoryCollectionName, key1);
        Console.WriteLine(lookup != null ? lookup.Metadata.Text : "ERROR: memory not found");

        Console.WriteLine("== Similarity Searching Memories: My favorite color is orange ==");
        var searchResults = kernel.Memory.SearchAsync(MemoryCollectionName, "My favorite color is orange", limit: 3, minRelevanceScore: 0.6);

        await foreach (var item in searchResults)
        {
            Console.WriteLine(item.Metadata.Text + " : " + item.Relevance);
        }

        Console.WriteLine("== Removing Collection {0} ==", MemoryCollectionName);
        await memoryStore.DeleteCollectionAsync(MemoryCollectionName);

        Console.WriteLine("== Printing Collections in DB ==");
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }
    }
}
