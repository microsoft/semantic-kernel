// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;
using Microsoft.SemanticKernel.Memory;
using RepoUtils;

// ReSharper disable once InconsistentNaming
/// <summary>
///  This example shows how to use the PineconeMemoryStore to store and retrieve memories with Pinecone assuming
///  you have a Pinecone account and have created an index. You can create an index using the Pinecone UI or
///  instead initialize the index using <see cref="IPineconeClient.CreateIndexAsync(IndexDefinition, System.Threading.CancellationToken)"/>.
///  But note that it can take a few minutes for the index to be ready for use.
/// </summary>
public static class Example38_Pinecone
{
    private const string MemoryCollectionName = "pinecone-test";

    public static async Task RunAsync()
    {
        string apiKey = TestConfiguration.Pinecone.ApiKey;
        string pineconeEnvironment = TestConfiguration.Pinecone.Environment;

        PineconeMemoryStore memoryStore = new(pineconeEnvironment, apiKey);

        IKernel kernel = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .WithOpenAITextEmbeddingGenerationService(TestConfiguration.OpenAI.EmbeddingModelId, TestConfiguration.OpenAI.ApiKey)
            .WithMemoryStorage(memoryStore)
            //.WithPineconeMemoryStore(pineconeEnvironment, apiKey) // This method offers an alternative approach to registering Pinecone memory storage.
            .Build();

        Console.WriteLine("== Printing Collections in DB ==");

        IAsyncEnumerable<string> collections = memoryStore.GetCollectionsAsync();

        await foreach (string collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Adding Memories ==");

        Dictionary<string, object> metadata = new()
        {
            { "type", "text" },
            { "tags", new List<string>() { "memory", "cats" } }
        };

        string additionalMetadata = System.Text.Json.JsonSerializer.Serialize(metadata);

        string key1 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, "british short hair", "cat1", null, additionalMetadata);
        string key2 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, "orange tabby", "cat2", null, additionalMetadata);
        string key3 = await kernel.Memory.SaveInformationAsync(MemoryCollectionName, "norwegian forest cat", "cat3", null, additionalMetadata);

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
        IAsyncEnumerable<MemoryQueryResult> searchResults = kernel.Memory.SearchAsync(MemoryCollectionName, "My favorite color is orange", 1, 0.8);

        await foreach (MemoryQueryResult item in searchResults)
        {
            Console.WriteLine(item.Metadata.Text + " : " + item.Relevance);
        }
    }
}
