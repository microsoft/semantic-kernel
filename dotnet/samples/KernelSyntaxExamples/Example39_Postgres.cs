// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Memory.Postgres;
using Microsoft.SemanticKernel.Memory;
using Npgsql;
using Pgvector.Npgsql;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example39_Postgres
{
    private const string MemoryCollectionName = "postgres_test";

    public static async Task RunAsync()
    {
        NpgsqlDataSourceBuilder dataSourceBuilder = new(Env.Var("POSTGRES_CONNECTIONSTRING"));
        dataSourceBuilder.UseVector();
        await using NpgsqlDataSource dataSource = dataSourceBuilder.Build();

        PostgresMemoryStore memoryStore = new(dataSource, vectorSize: 1536, schema: "public");

        IKernel kernel = Kernel.Builder
            .WithLogger(ConsoleLogger.Log)
            .WithOpenAITextCompletionService("text-davinci-003", Env.Var("OPENAI_API_KEY"))
            .WithOpenAITextEmbeddingGenerationService("text-embedding-ada-002", Env.Var("OPENAI_API_KEY"))
            .WithMemoryStorage(memoryStore)
            //.WithPostgresMemoryStore(dataSource, vectorSize: 1536, schema: "public") // This method offers an alternative approach to registering Postgres memory store.
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
