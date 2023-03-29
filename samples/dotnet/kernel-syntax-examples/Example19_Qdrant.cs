// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example19_Qdrant
{
    private const string MemoryCollectionName = "qdrant-test";

    public static async Task RunAsync()
    {
        var memoryStore = new QdrantMemoryStore(Env.Var("QDRANT_ENDPOINT"), int.Parse(Env.Var("QDRANT_PORT")));
        var kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Log)
            .Configure(c =>
            {
                c.AddAzureOpenAITextCompletion(serviceId: "davinci",
                    deploymentName: "text-davinci-003",
                    endpoint: Env.Var("AZURE_ENDPOINT"),
                    apiKey: Env.Var("AZURE_API_KEY"));
                c.AddAzureOpenAIEmbeddingGeneration(serviceId: "ada",
                    deploymentName: "text-embedding-ada-002",
                    endpoint: Env.Var("AZURE_ENDPOINT"),
                    apiKey: Env.Var("AZURE_API_KEY"));
            })
            .WithMemoryStorage(memoryStore)
            .Build();

        Console.WriteLine("== Printing Collections in DB ==");
        var collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Adding Memories ==");

        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "cat1", text: "british short hair");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "cat2", text: "orange tabby");
        await kernel.Memory.SaveInformationAsync(MemoryCollectionName, id: "cat3", text: "norwegian forest cat");

        Console.WriteLine("== Printing Collections in DB ==");
        collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }

        Console.WriteLine("== Retrieving Memories ==");
        var lookup = await kernel.Memory.GetAsync(MemoryCollectionName, "cat1");

        if (lookup == null)
        {
            Console.WriteLine("No memories found");
        }
        else
        {
            Console.WriteLine(lookup.Metadata.Text);
        }

        Console.WriteLine("== Removing Collection {0} ==", MemoryCollectionName);
        Console.WriteLine("== Printing Collections in DB ==");
        await memoryStore.DeleteCollectionAsync(MemoryCollectionName);
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }
    }
}
