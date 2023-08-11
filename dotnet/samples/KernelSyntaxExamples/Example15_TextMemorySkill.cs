// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;
using Microsoft.SemanticKernel.Connectors.Memory.DuckDB;
using Microsoft.SemanticKernel.Connectors.Memory.Kusto;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;
using Microsoft.SemanticKernel.Connectors.Memory.Postgres;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Connectors.Memory.Redis;
using Microsoft.SemanticKernel.Connectors.Memory.Sqlite;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Core;
using Npgsql;
using Pgvector.Npgsql;
using RepoUtils;
using StackExchange.Redis;

// ReSharper disable once InconsistentNaming
public static class Example15_TextMemorySkill
{
    private const string MemoryCollectionName = "aboutMe";

    public static async Task RunAsync(CancellationToken cancellationToken = default)
    {
        IMemoryStore store;

        ///////////////////////////////////////////////////////////////////////////////////////////
        // INSTRUCTIONS: uncomment one of the following lines to select the memory store to use. //
        ///////////////////////////////////////////////////////////////////////////////////////////

        // Volatile Memory Store - an in-memory store that is not persisted
        store = new VolatileMemoryStore();

        // Sqlite Memory Store - a file-based store that persists data in a Sqlite database
        // store = await CreateSampleSqliteMemoryStoreAsync();

        // DuckDB Memory Store - a file-based store that persists data in a DuckDB database
        // store = await CreateSampleDuckDbMemoryStoreAsync();

        // Azure Cognitive Search Memory Store - a store that persists data in a hosted Azure Cognitive Search database
        // store = CreateSampleAzureCognitiveSearchMemoryStore();

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
        // store = await CreateSamplePostgresMemoryStoreAsync();

        // Kusto Memory Store
        // store = await CreateSampleKustoMemoryStoreAsync();

        await RunWithStoreAsync(store, cancellationToken);
    }

    private static async Task<IMemoryStore> CreateSampleSqliteMemoryStoreAsync()
    {
        IMemoryStore store = await SqliteMemoryStore.ConnectAsync("memories.sqlite");
        return store;
    }

    private static async Task<IMemoryStore> CreateSampleDuckDbMemoryStoreAsync()
    {
        IMemoryStore store = await DuckDBMemoryStore.ConnectAsync("memories.duckdb");
        return store;
    }

    private static IMemoryStore CreateSampleAzureCognitiveSearchMemoryStore()
    {
        IMemoryStore store = new AzureCognitiveSearchMemoryStore(TestConfiguration.ACS.Endpoint, TestConfiguration.ACS.ApiKey);
        return store;
    }

    private static IMemoryStore CreateSampleChromaMemoryStore()
    {
        IMemoryStore store = new ChromaMemoryStore(TestConfiguration.Chroma.Endpoint, ConsoleLogger.Logger);
        return store;
    }

    private static IMemoryStore CreateSampleQdrantMemoryStore()
    {
        IMemoryStore store = new QdrantMemoryStore(TestConfiguration.Qdrant.Endpoint, 1536, ConsoleLogger.Logger);
        return store;
    }

    private static IMemoryStore CreateSamplePineconeMemoryStore()
    {
        IMemoryStore store = new PineconeMemoryStore(TestConfiguration.Pinecone.Environment, TestConfiguration.Pinecone.ApiKey, ConsoleLogger.Logger);
        return store;
    }

    private static IMemoryStore CreateSampleWeaviateMemoryStore()
    {
        IMemoryStore store = new WeaviateMemoryStore(TestConfiguration.Weaviate.Endpoint, TestConfiguration.Weaviate.ApiKey);
        return store;
    }

    private static async Task<IMemoryStore> CreateSampleRedisMemoryStoreAsync()
    {
        string configuration = TestConfiguration.Redis.Configuration;
        await using ConnectionMultiplexer connectionMultiplexer = await ConnectionMultiplexer.ConnectAsync(configuration);
        IDatabase database = connectionMultiplexer.GetDatabase();
        IMemoryStore store = new RedisMemoryStore(database, vectorSize: 1536);
        return store;
    }

    private static async Task<IMemoryStore> CreateSamplePostgresMemoryStoreAsync()
    {
        NpgsqlDataSourceBuilder dataSourceBuilder = new(TestConfiguration.Postgres.ConnectionString);
        dataSourceBuilder.UseVector();
        await using NpgsqlDataSource dataSource = dataSourceBuilder.Build();
        IMemoryStore store = new PostgresMemoryStore(dataSource, vectorSize: 1536, schema: "public");
        return store;
    }

    private static IMemoryStore CreateSampleKustoMemoryStore()
    {
        var connectionString = new Kusto.Data.KustoConnectionStringBuilder(TestConfiguration.Kusto.ConnectionString).WithAadUserPromptAuthentication();
        IMemoryStore store = new KustoMemoryStore(connectionString, "MyDatabase");
        return store;
    }

    private static async Task RunWithStoreAsync(IMemoryStore memoryStore, CancellationToken cancellationToken)
    {
        var logger = ConsoleLogger.Logger;

        var kernel = Kernel.Builder
            .WithLogger(logger)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .WithOpenAITextEmbeddingGenerationService(TestConfiguration.OpenAI.EmbeddingModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var embeddingGenerator = kernel.GetService<ITextEmbeddingGeneration>();

        using SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

        // ========= Store memories using the ISemanticTextMemory object itself =========

        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info1", text: "My name is Andrea", cancellationToken: cancellationToken);
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info2", text: "I work as a tourist operator", cancellationToken: cancellationToken);
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info3", text: "I've been living in Seattle since 2005", cancellationToken: cancellationToken);
        await textMemory.SaveInformationAsync(MemoryCollectionName, id: "info4", text: "I visited France and Italy five times since 2015", cancellationToken: cancellationToken);

        // ========= Store memories using semantic function =========

        // Add Memory as a skill for other functions
        var memorySkill = new TextMemorySkill(textMemory);
        kernel.ImportSkill(memorySkill);

        // Build a semantic function that saves info to memory
        const string SaveFunctionDefinition = "{{save $info}}";
        var memorySaver = kernel.CreateSemanticFunction(SaveFunctionDefinition);

        await kernel.RunAsync(memorySaver, new()
        {
            [TextMemorySkill.CollectionParam] = MemoryCollectionName,
            [TextMemorySkill.KeyParam] = "info5",
            ["info"] = "My family is from New York"
        }, cancellationToken);

        // ========= Test memory remember =========
        Console.WriteLine("========= Example: Recalling a Memory =========");

        var answer = await memorySkill.RetrieveAsync(MemoryCollectionName, "info1", logger: logger, cancellationToken: cancellationToken);
        Console.WriteLine("Memory associated with 'info1': {0}", answer);
        /*
        Output:
        "Memory associated with 'info1': My name is Andrea
        */

        // ========= Test memory recall =========
        Console.WriteLine("========= Example: Recalling an Idea =========");

        answer = await memorySkill.RecallAsync("where did I grow up?", MemoryCollectionName, relevance: null, limit: 2, logger: logger, cancellationToken: cancellationToken);
        Console.WriteLine("Ask: where did I grow up?");
        Console.WriteLine("Answer:\n{0}", answer);

        answer = await memorySkill.RecallAsync("where do I live?", MemoryCollectionName, relevance: null, limit: 2, logger: logger, cancellationToken: cancellationToken);
        Console.WriteLine("Ask: where do I live?");
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

Question: {{$input}}

Answer:
";

        var aboutMeOracle = kernel.CreateSemanticFunction(RecallFunctionDefinition, maxTokens: 100);

        var result = await kernel.RunAsync(aboutMeOracle, new("Do I live in the same town where I grew up?")
        {
            [TextMemorySkill.CollectionParam] = MemoryCollectionName,
            [TextMemorySkill.RelevanceParam] = "0.8"
        }, cancellationToken);

        Console.WriteLine("Do I live in the same town where I grew up?\n");
        Console.WriteLine(result);

        /*
        Output:

            Do I live in the same town where I grew up?

            No, I do not live in the same town where I grew up since my family is from New York and I have been living in Seattle since 2005.
        */

        // ========= Remove a memory =========
        Console.WriteLine("========= Example: Forgetting a Memory =========");

        result = await kernel.RunAsync(aboutMeOracle, new("Tell me a bit about myself")
        {
            ["fact1"] = "What is my name?",
            ["fact2"] = "What do I do for a living?",
            [TextMemorySkill.RelevanceParam] = ".75"
        }, cancellationToken);

        Console.WriteLine("Tell me a bit about myself\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            My name is Andrea and my family is from New York. I work as a tourist operator.
        */

        await memorySkill.RemoveAsync(MemoryCollectionName, "info1", logger: logger, cancellationToken: cancellationToken);

        result = await kernel.RunAsync(aboutMeOracle, new("Tell me a bit about myself"), cancellationToken);

        Console.WriteLine("Tell me a bit about myself\n");
        Console.WriteLine(result);

        /*
        Approximate Output:
            Tell me a bit about myself

            I'm from a family originally from New York and I work as a tourist operator. I've been living in Seattle since 2005.
        */
    }
}
