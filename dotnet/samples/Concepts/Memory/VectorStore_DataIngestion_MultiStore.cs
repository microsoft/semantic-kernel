﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;
using StackExchange.Redis;

namespace Memory;

/// <summary>
/// An example showing how to ingest data into a vector store using <see cref="RedisVectorStore"/>, <see cref="QdrantVectorStore"/> or <see cref="VolatileVectorStore"/>.
/// Since Redis and Volatile supports string keys and Qdrant supports ulong or Guid keys, this example also shows how you can have common code
/// that works with both types of keys by using a generic key generator function.
///
/// The example shows the following steps:
/// 1. Register a vector store and embedding generator with the DI container.
/// 2. Register a class (DataIngestor) with the DI container that uses the vector store and embedding generator to ingest data.
/// 3. Ingest some data into the vector store.
/// 4. Read the data back from the vector store.
///
/// For some databases in this sample (Redis &amp; Qdrant), you need a local instance of Docker running, since the associated fixtures will try and start containers in the local docker instance to run against.
/// </summary>
[Collection("Sequential")]
public class VectorStore_DataIngestion_MultiStore(ITestOutputHelper output, VectorStoreRedisContainerFixture redisFixture, VectorStoreQdrantContainerFixture qdrantFixture) : BaseTest(output), IClassFixture<VectorStoreRedisContainerFixture>, IClassFixture<VectorStoreQdrantContainerFixture>
{
    /// <summary>
    /// Example with dependency injection.
    /// </summary>
    /// <param name="databaseType">The type of database to run the example for.</param>
    [Theory]
    [InlineData("Redis")]
    [InlineData("Qdrant")]
    [InlineData("Volatile")]
    public async Task ExampleWithDIAsync(string databaseType)
    {
        // Use the kernel for DI purposes.
        var kernelBuilder = Kernel
            .CreateBuilder();

        // Register an embedding generation service with the DI container.
        kernelBuilder.AddAzureOpenAITextEmbeddingGeneration(
            deploymentName: TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            endpoint: TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            apiKey: TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        // Register the chosen vector store with the DI container and initialize docker containers via the fixtures where needed.
        if (databaseType == "Redis")
        {
            await redisFixture.ManualInitializeAsync();
            kernelBuilder.AddRedisVectorStore("localhost:6379");
        }
        else if (databaseType == "Qdrant")
        {
            await qdrantFixture.ManualInitializeAsync();
            kernelBuilder.AddQdrantVectorStore("localhost");
        }
        else if (databaseType == "Volatile")
        {
            kernelBuilder.AddVolatileVectorStore();
        }

        // Register the DataIngestor with the DI container.
        kernelBuilder.Services.AddTransient<DataIngestor>();

        // Build the kernel.
        var kernel = kernelBuilder.Build();

        // Build a DataIngestor object using the DI container.
        var dataIngestor = kernel.GetRequiredService<DataIngestor>();

        // Invoke the data ingestor using an appropriate key generator function for each database type.
        // Redis and Volatile supports string keys, while Qdrant supports ulong or Guid keys, so we use a different key generator for each key type.
        if (databaseType == "Redis" || databaseType == "Volatile")
        {
            await this.UpsertDataAndReadFromVectorStoreAsync(dataIngestor, () => Guid.NewGuid().ToString());
        }
        else if (databaseType == "Qdrant")
        {
            await this.UpsertDataAndReadFromVectorStoreAsync(dataIngestor, () => Guid.NewGuid());
        }
    }

    /// <summary>
    /// Example without dependency injection.
    /// </summary>
    /// <param name="databaseType">The type of database to run the example for.</param>
    [Theory]
    [InlineData("Redis")]
    [InlineData("Qdrant")]
    [InlineData("Volatile")]
    public async Task ExampleWithoutDIAsync(string databaseType)
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        // Construct the chosen vector store and initialize docker containers via the fixtures where needed.
        IVectorStore vectorStore;
        if (databaseType == "Redis")
        {
            await redisFixture.ManualInitializeAsync();
            var database = ConnectionMultiplexer.Connect("localhost:6379").GetDatabase();
            vectorStore = new RedisVectorStore(database);
        }
        else if (databaseType == "Qdrant")
        {
            await qdrantFixture.ManualInitializeAsync();
            var qdrantClient = new QdrantClient("localhost");
            vectorStore = new QdrantVectorStore(qdrantClient);
        }
        else if (databaseType == "Volatile")
        {
            vectorStore = new VolatileVectorStore();
        }
        else
        {
            throw new ArgumentException("Invalid database type.");
        }

        // Create the DataIngestor.
        var dataIngestor = new DataIngestor(vectorStore, textEmbeddingGenerationService);

        // Invoke the data ingestor using an appropriate key generator function for each database type.
        // Redis and Volatile supports string keys, while Qdrant supports ulong or Guid keys, so we use a different key generator for each key type.
        if (databaseType == "Redis" || databaseType == "Volatile")
        {
            await this.UpsertDataAndReadFromVectorStoreAsync(dataIngestor, () => Guid.NewGuid().ToString());
        }
        else if (databaseType == "Qdrant")
        {
            await this.UpsertDataAndReadFromVectorStoreAsync(dataIngestor, () => Guid.NewGuid());
        }
    }

    private async Task UpsertDataAndReadFromVectorStoreAsync<TKey>(DataIngestor dataIngestor, Func<TKey> uniqueKeyGenerator)
            where TKey : notnull
    {
        // Ingest some data into the vector store.
        var upsertedKeys = await dataIngestor.ImportDataAsync(uniqueKeyGenerator);

        // Get one of the upserted records.
        var upsertedRecord = await dataIngestor.GetGlossaryAsync(upsertedKeys.First());

        // Write upserted keys and one of the upserted records to the console.
        Console.WriteLine($"Upserted keys: {string.Join(", ", upsertedKeys)}");
        Console.WriteLine($"Upserted record: {JsonSerializer.Serialize(upsertedRecord)}");
    }

    /// <summary>
    /// Sample class that does ingestion of sample data into a vector store and allows retrieval of data from the vector store.
    /// </summary>
    /// <param name="vectorStore">The vector store to ingest data into.</param>
    /// <param name="textEmbeddingGenerationService">Used to generate embeddings for the data being ingested.</param>
    private sealed class DataIngestor(IVectorStore vectorStore, ITextEmbeddingGenerationService textEmbeddingGenerationService)
    {
        /// <summary>
        /// Create some glossary entries and upsert them into the vector store.
        /// </summary>
        /// <returns>The keys of the upserted glossary entries.</returns>
        /// <typeparam name="TKey">The type of the keys in the vector store.</typeparam>
        public async Task<IEnumerable<TKey>> ImportDataAsync<TKey>(Func<TKey> uniqueKeyGenerator)
            where TKey : notnull
        {
            // Get and create collection if it doesn't exist.
            var collection = vectorStore.GetCollection<TKey, Glossary<TKey>>("skglossary");
            await collection.CreateCollectionIfNotExistsAsync();

            // Create glossary entries and generate embeddings for them.
            var glossaryEntries = CreateGlossaryEntries(uniqueKeyGenerator).ToList();
            var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
            {
                entry.DefinitionEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Definition);
            }));
            await Task.WhenAll(tasks);

            // Upsert the glossary entries into the collection and return their keys.
            var upsertedKeys = glossaryEntries.Select(x => collection.UpsertAsync(x));
            return await Task.WhenAll(upsertedKeys);
        }

        /// <summary>
        /// Get a glossary entry from the vector store.
        /// </summary>
        /// <param name="key">The key of the glossary entry to retrieve.</param>
        /// <returns>The glossary entry.</returns>
        /// <typeparam name="TKey">The type of the keys in the vector store.</typeparam>
        public Task<Glossary<TKey>?> GetGlossaryAsync<TKey>(TKey key)
            where TKey : notnull
        {
            var collection = vectorStore.GetCollection<TKey, Glossary<TKey>>("skglossary");
            return collection.GetAsync(key, new() { IncludeVectors = true });
        }
    }

    /// <summary>
    /// Create some sample glossary entries.
    /// </summary>
    /// <typeparam name="TKey">The type of the model key.</typeparam>
    /// <param name="uniqueKeyGenerator">A function that can be used to generate unique keys for the model in the type that the model requires.</param>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<Glossary<TKey>> CreateGlossaryEntries<TKey>(Func<TKey> uniqueKeyGenerator)
    {
        yield return new Glossary<TKey>
        {
            Key = uniqueKeyGenerator(),
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary<TKey>
        {
            Key = uniqueKeyGenerator(),
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary<TKey>
        {
            Key = uniqueKeyGenerator(),
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)."
        };
    }

    /// <summary>
    /// Sample model class that represents a glossary entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    /// <typeparam name="TKey">The type of the model key.</typeparam>
    private sealed class Glossary<TKey>
    {
        [VectorStoreRecordKey]
        public TKey Key { get; set; }

        [VectorStoreRecordData]
        public string Term { get; set; }

        [VectorStoreRecordData]
        public string Definition { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }
}
