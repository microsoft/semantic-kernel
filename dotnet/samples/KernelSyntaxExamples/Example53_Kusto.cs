// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Memory.Kusto;
using Microsoft.SemanticKernel.Memory;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example53_Kusto
{
    private const string MemoryCollectionName = "kusto_test";

    public static async Task RunAsync()
    {
        var connectionString = new Kusto.Data.KustoConnectionStringBuilder(TestConfiguration.Kusto.ConnectionString).WithAadUserPromptAuthentication();
        using KustoMemoryStore memoryStore = new(connectionString, "MyDatabase");

        IKernel kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Logger)
            .WithOpenAITextCompletionService(
                modelId: TestConfiguration.OpenAI.ModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .WithOpenAITextEmbeddingGenerationService(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .WithMemoryStorage(memoryStore)
            //.WithMemoryStorage(new KustoMemoryStore(new Kusto.Data.KustoConnectionStringBuilder(TestConfiguration.Kusto.ConnectionString).WithAadUserPromptAuthentication(), "MyDatabase"))
            .Build();

        Console.WriteLine("== Printing Collections in DB ==");
        var collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Adding Memories ==");

        var key1 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "cat1", text: "british short hair");
        var key2 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "cat2", text: "orange tabby");
        var key3 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "cat3", text: "norwegian forest cat");

        Console.WriteLine("== Printing Collections in DB ==");
        collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Retrieving Memories Through the Kernel ==");
        MemoryQueryResult? lookup = await kernel.Memory.GetAsync(MemoryCollectionName, "cat1");
        Console.WriteLine(lookup != null ? lookup.Metadata.Text : "ERROR: memory not found");

        Console.WriteLine("== Retrieving Memories Directly From the Store ==");
        var memory1 = await memoryStore.GetAsync(MemoryCollectionName, key1);
        var memory2 = await memoryStore.GetAsync(MemoryCollectionName, key2);
        var memory3 = await memoryStore.GetAsync(MemoryCollectionName, key3);
        Console.WriteLine(memory1 != null ? memory1.Metadata.Text : "ERROR: memory not found");
        Console.WriteLine(memory2 != null ? memory2.Metadata.Text : "ERROR: memory not found");
        Console.WriteLine(memory3 != null ? memory3.Metadata.Text : "ERROR: memory not found");

        Console.WriteLine("== Similarity Searching Memories: My favorite color is orange ==");
        var searchResults = kernel.Memory.SearchAsync(MemoryCollectionName, "My favorite color is orange", limit: 3, minRelevanceScore: 0.8);

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
