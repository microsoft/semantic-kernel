// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.AI.OpenAI;
using Azure.Identity;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;

namespace Memory;

/// <summary>
/// A simple example showing how to ingest data into a vector store using <see cref="QdrantVectorStore"/>.
///
/// The example shows the following steps:
/// 1. Create an embedding generator.
/// 2. Create a Qdrant Vector Store.
/// 3. Ingest some data into the vector store.
/// 4. Read the data back from the vector store.
///
/// You need a local instance of Docker running, since the associated fixture will try and start a Qdrant container in the local docker instance to run against.
/// </summary>
[Collection("Sequential")]
public class VectorStore_DataIngestion_Simple(ITestOutputHelper output, VectorStoreQdrantContainerFixture qdrantFixture) : BaseTest(output), IClassFixture<VectorStoreQdrantContainerFixture>
{
    [Fact]
    public async Task ExampleAsync()
    {
        // Create an embedding generation service.
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Initiate the docker container and construct the vector store.
        await qdrantFixture.ManualInitializeAsync();
        var vectorStore = new QdrantVectorStore(new QdrantClient("localhost"), ownsClient: true);

        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<ulong, Glossary>("skglossary");
        await collection.EnsureCollectionExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGlossaryEntries().ToList();
        var keys = glossaryEntries.Select(entry => entry.Key).ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.DefinitionEmbedding = (await embeddingGenerator.GenerateAsync(entry.Definition)).Vector;
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        await collection.UpsertAsync(glossaryEntries);

        // Retrieve one of the upserted records from the collection.
        var upsertedRecord = await collection.GetAsync(keys.First(), new() { IncludeVectors = true });

        // Write upserted keys and one of the upserted records to the console.
        Console.WriteLine($"Upserted record: {JsonSerializer.Serialize(upsertedRecord)}");
    }

    /// <summary>
    /// Sample model class that represents a glossary entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    private sealed class Glossary
    {
        [VectorStoreKey]
        public ulong Key { get; set; }

        [VectorStoreData]
        public string Term { get; set; }

        [VectorStoreData]
        public string Definition { get; set; }

        [VectorStoreVector(1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }

    /// <summary>
    /// Create some sample glossary entries.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<Glossary> CreateGlossaryEntries()
    {
        yield return new Glossary
        {
            Key = 1,
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary
        {
            Key = 2,
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary
        {
            Key = 3,
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)."
        };
    }
}
