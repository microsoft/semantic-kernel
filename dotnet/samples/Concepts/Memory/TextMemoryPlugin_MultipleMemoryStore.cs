﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.Chroma;
using Microsoft.SemanticKernel.Connectors.DuckDB;
using Microsoft.SemanticKernel.Connectors.Kusto;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Npgsql;
using StackExchange.Redis;

namespace Memory;

public class TextMemoryPlugin_MultipleMemoryStore(ITestOutputHelper output) : BaseTest(output)
{
    private const string MemoryCollectionName = "aboutMe";

    [Theory]
    [InlineData("Volatile")]
    [InlineData("AzureAISearch")]
    public async Task RunAsync(string provider)
    {
        // Volatile Memory Store - an in-memory store that is not persisted
        IMemoryStore store = provider switch
        {
            "AzureAISearch" => CreateSampleAzureAISearchMemoryStore(),
            _ => new VolatileMemoryStore(),
        };

        ///////////////////////////////////////////////////////////////////////////////////////////////////
        // INSTRUCTIONS: uncomment one of the following lines to select a different memory store to use. //
        ///////////////////////////////////////////////////////////////////////////////////////////////////

        // Sqlite Memory Store - a file-based store that persists data in a Sqlite database
        // store = await CreateSampleSqliteMemoryStoreAsync();

        // DuckDB Memory Store - a file-based store that persists data in a DuckDB database
        // store = await CreateSampleDuckDbMemoryStoreAsync();

        // MongoDB Memory Store - a store that persists data in a MongoDB database
        // store = CreateSampleMongoDBMemoryStore();

        // Azure AI Search Memory Store - a store that persists data in a hosted Azure AI Search database
        // store = CreateSampleAzureAISearchMemoryStore();

        // Qdrant Memory Store - a store that persists data in a local or remote Qdrant database
        // store = CreateSampleQdrantMemoryStore();

        // Chroma Memory Store
        // store = CreateSampleChromaMemoryStore();

        // Pinecone Memory Store - a store that persists data in a hosted Pinecone database
        // store = CreateSamplePineconeMemoryStore();

        // Weaviate Memory Store
        // store = CreateSampleWeaviateMemoryStore();

        // Redis Memory Store
        // store = await CreateSampleRedisMemoryStoreAsync();

        // Postgres Memory Store
        // store = CreateSamplePostgresMemoryStore();

        // Kusto Memory Store
        // store = CreateSampleKustoMemoryStore();

        await RunWithStoreAsync(store);
    }

    private async Task<IMemoryStore> CreateSampleSqliteMemoryStoreAsync()
    {
        IMemoryStore store = await SqliteMemoryStore.ConnectAsync("memories.sqlite");
        return store;
    }

    private async Task<IMemoryStore> CreateSampleDuckDbMemoryStoreAsync()
    {
        IMemoryStore store = await DuckDBMemoryStore.ConnectAsync("memories.duckdb", 1536);
        return store;
    }

    private IMemoryStore CreateSampleMongoDBMemoryStore()
    {
        IMemoryStore store = new MongoDBMemoryStore(TestConfiguration.MongoDB.ConnectionString, "memoryPluginExample");
        return store;
    }

    private IMemoryStore CreateSampleAzureAISearchMemoryStore()
    {
        IMemoryStore store = new AzureAISearchMemoryStore(TestConfiguration.AzureAISearch.Endpoint, TestConfiguration.AzureAISearch.ApiKey);
        return store;
    }

    private IMemoryStore CreateSampleChromaMemoryStore()
    {
        IMemoryStore store = new ChromaMemoryStore(TestConfiguration.Chroma.Endpoint, this.LoggerFactory);
        return store;
    }

    private IMemoryStore CreateSampleQdrantMemoryStore()
    {
        IMemoryStore store = new QdrantMemoryStore(TestConfiguration.Qdrant.Endpoint, 1536, this.LoggerFactory);
        return store;
    }

    private IMemoryStore CreateSamplePineconeMemoryStore()
    {
        IMemoryStore store = new PineconeMemoryStore(TestConfiguration.Pinecone.Environment, TestConfiguration.Pinecone.ApiKey, this.LoggerFactory);
        return store;
    }

    private IMemoryStore CreateSampleWeaviateMemoryStore()
    {
        IMemoryStore store = new WeaviateMemoryStore(TestConfiguration.Weaviate.Endpoint, TestConfiguration.Weaviate.ApiKey);
        return store;
    }

    private async Task<IMemoryStore> CreateSampleRedisMemoryStoreAsync()
    {
        string configuration = TestConfiguration.Redis.Configuration;
        ConnectionMultiplexer connectionMultiplexer = await ConnectionMultiplexer.ConnectAsync(configuration);
        IDatabase database = connectionMultiplexer.GetDatabase();
        IMemoryStore store = new RedisMemoryStore(database, vectorSize: 1536);
        return store;
    }

    private static IMemoryStore CreateSamplePostgresMemoryStore()
    {
        NpgsqlDataSourceBuilder dataSourceBuilder = new(TestConfiguration.Postgres.ConnectionString);
        dataSourceBuilder.UseVector();
        NpgsqlDataSource dataSource = dataSourceBuilder.Build();
        IMemoryStore store = new PostgresMemoryStore(dataSource, vectorSize: 1536, schema: "public");
        return store;
    }

    private static IMemoryStore CreateSampleKustoMemoryStore()
    {
        var connectionString = new Kusto.Data.KustoConnectionStringBuilder(TestConfiguration.Kusto.ConnectionString).WithAadUserPromptAuthentication();
        IMemoryStore store = new KustoMemoryStore(connectionString, "MyDatabase");
        return store;
    }

    private async Task RunWithStoreAsync(IMemoryStore memoryStore)
    {
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .AddOpenAITextEmbeddingGeneration(TestConfiguration.OpenAI.EmbeddingModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create an embedding generator to use for semantic memory.
        var embeddingGenerator = new OpenAITextEmbeddingGenerationService(TestConfiguration.OpenAI.EmbeddingModelId, TestConfiguration.OpenAI.ApiKey);

        // The combination of the text embedding generator and the memory store makes up the 'SemanticTextMemory' object used to
        // store and retrieve memories.
        SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

        /////////////////////////////////////////////////////////////////////////////////////////////////////
        // PART 1: Store and retrieve memories using the ISemanticTextMemory (textMemory) object.
        //
        // This is a simple way to store memories from a code perspective, without using the Kernel.
        /////////////////////////////////////////////////////////////////////////////////////////////////////
        Console.WriteLine("== PART 1a: Saving Memories through the ISemanticTextMemory object ==");

        Console.WriteLine("Saving memory with key 'info1': \"My name is Andrea\"");
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info1", text: "My name is Andrea");

        Console.WriteLine("Saving memory with key 'info2': \"I work as a tourist operator\"");
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info2", text: "I work as a tourist operator");

        Console.WriteLine("Saving memory with key 'info3': \"I've been living in Seattle since 2005\"");
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info3", text: "I've been living in Seattle since 2005");

        Console.WriteLine("Saving memory with key 'info4': \"I visited France and Italy five times since 2015\"");
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info4", text: "I visited France and Italy five times since 2015");

        // Retrieve a memory
        Console.WriteLine("== PART 1b: Retrieving Memories through the ISemanticTextMemory object ==");
        MemoryQueryResult? lookup = await textMemory.GetAsync(MemoryCollectionName, "info1");
        Console.WriteLine("Memory with key 'info1':" + lookup?.Metadata.Text ?? "ERROR: memory not found");
        Console.WriteLine();

        /////////////////////////////////////////////////////////////////////////////////////////////////////
        // PART 2: Create TextMemoryPlugin, store and retrieve memories through the Kernel.
        //
        // This enables prompt functions and the AI (via Planners) to access memories
        /////////////////////////////////////////////////////////////////////////////////////////////////////

        Console.WriteLine("== PART 2a: Saving Memories through the Kernel with TextMemoryPlugin and the 'Save' function ==");

        // Import the TextMemoryPlugin into the Kernel for other functions
        var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));

        // Save a memory with the Kernel
        Console.WriteLine("Saving memory with key 'info5': \"My family is from New York\"");
        await kernel.InvokeAsync(memoryPlugin["Save"], new()
        {
            [TextMemoryPlugin.InputParam] = "My family is from New York",
            [TextMemoryPlugin.CollectionParam] = MemoryCollectionName,
            [TextMemoryPlugin.KeyParam] = "info5",
        });

        // Retrieve a specific memory with the Kernel
        Console.WriteLine("== PART 2b: Retrieving Memories through the Kernel with TextMemoryPlugin and the 'Retrieve' function ==");
        var result = await kernel.InvokeAsync(memoryPlugin["Retrieve"], new KernelArguments()
        {
            [TextMemoryPlugin.CollectionParam] = MemoryCollectionName,
            [TextMemoryPlugin.KeyParam] = "info5"
        });

        Console.WriteLine("Memory with key 'info5':" + result.GetValue<string>() ?? "ERROR: memory not found");
        Console.WriteLine();

        /////////////////////////////////////////////////////////////////////////////////////////////////////
        // PART 3: Recall similar ideas with semantic search
        //
        // Uses AI Embeddings for fuzzy lookup of memories based on intent, rather than a specific key.
        /////////////////////////////////////////////////////////////////////////////////////////////////////

        Console.WriteLine("== PART 3: Recall (similarity search) with AI Embeddings ==");

        Console.WriteLine("== PART 3a: Recall (similarity search) with ISemanticTextMemory ==");
        Console.WriteLine("Ask: where did I grow up?");

        await foreach (var answer in textMemory.SearchAsync(
            collection: MemoryCollectionName,
            query: "where did I grow up?",
            limit: 2,
            minRelevanceScore: 0.79,
            withEmbeddings: true))
        {
            Console.WriteLine($"Answer: {answer.Metadata.Text}");
        }

        Console.WriteLine("== PART 3b: Recall (similarity search) with Kernel and TextMemoryPlugin 'Recall' function ==");
        Console.WriteLine("Ask: where do I live?");

        result = await kernel.InvokeAsync(memoryPlugin["Recall"], new()
        {
            [TextMemoryPlugin.InputParam] = "Ask: where do I live?",
            [TextMemoryPlugin.CollectionParam] = MemoryCollectionName,
            [TextMemoryPlugin.LimitParam] = "2",
            [TextMemoryPlugin.RelevanceParam] = "0.79",
        });

        Console.WriteLine($"Answer: {result.GetValue<string>()}");
        Console.WriteLine();

        /*
        Output:

            Ask: where did I grow up?
            Answer:
                ["My family is from New York","I\u0027ve been living in Seattle since 2005"]

            Ask: where do I live?
            Answer:
                ["I\u0027ve been living in Seattle since 2005","My family is from New York"]
        */

        /////////////////////////////////////////////////////////////////////////////////////////////////////
        // PART 4: TextMemoryPlugin Recall in a Prompt Function
        //
        // Looks up related memories when rendering a prompt template, then sends the rendered prompt to
        // the text generation model to answer a natural language query.
        /////////////////////////////////////////////////////////////////////////////////////////////////////

        Console.WriteLine("== PART 4: Using TextMemoryPlugin 'Recall' function in a Prompt Function ==");

        // Build a prompt function that uses memory to find facts
        const string RecallFunctionDefinition = @"
Consider only the facts below when answering questions:

BEGIN FACTS
About me: {{recall 'where did I grow up?'}}
About me: {{recall 'where do I live now?'}}
END FACTS

Question: {{$input}}

Answer:
";

        var aboutMeOracle = kernel.CreateFunctionFromPrompt(RecallFunctionDefinition, new OpenAIPromptExecutionSettings() { MaxTokens = 100 });

        result = await kernel.InvokeAsync(aboutMeOracle, new()
        {
            [TextMemoryPlugin.InputParam] = "Do I live in the same town where I grew up?",
            [TextMemoryPlugin.CollectionParam] = MemoryCollectionName,
            [TextMemoryPlugin.LimitParam] = "2",
            [TextMemoryPlugin.RelevanceParam] = "0.79",
        });

        Console.WriteLine("Ask: Do I live in the same town where I grew up?");
        Console.WriteLine($"Answer: {result.GetValue<string>()}");

        /*
        Approximate Output:
            Answer: No, I do not live in the same town where I grew up since my family is from New York and I have been living in Seattle since 2005.
        */

        /////////////////////////////////////////////////////////////////////////////////////////////////////
        // PART 5: Cleanup, deleting database collection
        //
        /////////////////////////////////////////////////////////////////////////////////////////////////////

        Console.WriteLine("== PART 5: Cleanup, deleting database collection ==");

        Console.WriteLine("Printing Collections in DB...");
        var collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }
        Console.WriteLine();

        Console.WriteLine($"Removing Collection {MemoryCollectionName}");
        await memoryStore.DeleteCollectionAsync(MemoryCollectionName);
        Console.WriteLine();

        Console.WriteLine($"Printing Collections in DB (after removing {MemoryCollectionName})...");
        collections = memoryStore.GetCollectionsAsync();
        await foreach (var collection in collections)
        {
            Console.WriteLine(collection);
        }
    }
}
