// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace GettingStartedWithVectorStores;

/// <summary>
/// Example showing how to generate embeddings and ingest data into an in-memory vector store.
/// </summary>
public class Step1_Ingest_Data(ITestOutputHelper output, VectorStoresFixture fixture) : BaseTest(output), IClassFixture<VectorStoresFixture>
{
    /// <summary>
    /// Example showing how to ingest data into an in-memory vector store.
    /// </summary>
    [Fact]
    public async Task IngestDataIntoInMemoryVectorStoreAsync()
    {
        // Construct the vector store and get the collection.
        var vectorStore = new InMemoryVectorStore();
        var collection = vectorStore.GetCollection<string, Glossary>("skglossary");

        // Ingest data into the collection.
        await IngestDataIntoVectorStoreAsync(collection, fixture.EmbeddingGenerator);

        // Retrieve an item from the collection and write it to the console.
        var record = await collection.GetAsync("4");
        Console.WriteLine(record!.Definition);
    }

    /// <summary>
    /// Ingest data into the given collection.
    /// </summary>
    /// <param name="collection">The collection to ingest data into.</param>
    /// <param name="embeddingGenerator">The service to use for generating embeddings.</param>
    /// <returns>The keys of the upserted records.</returns>
    internal static async Task<IEnumerable<string>> IngestDataIntoVectorStoreAsync(
        VectorStoreCollection<string, Glossary> collection,
        IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator)
    {
        // Create the collection if it doesn't exist.
        await collection.EnsureCollectionExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGlossaryEntries().ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.DefinitionEmbedding = (await embeddingGenerator.GenerateAsync(entry.Definition)).Vector;
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        await collection.UpsertAsync(glossaryEntries);

        return glossaryEntries.Select(g => g.Key);
    }

    /// <summary>
    /// Create some sample glossary entries.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<Glossary> CreateGlossaryEntries()
    {
        yield return new Glossary
        {
            Key = "1",
            Category = "Software",
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary
        {
            Key = "2",
            Category = "Software",
            Term = "SDK",
            Definition = "Software development kit. A set of libraries and tools that allow software developers to build software more easily."
        };

        yield return new Glossary
        {
            Key = "3",
            Category = "SK",
            Term = "Connectors",
            Definition = "Semantic Kernel Connectors allow software developers to integrate with various services providing AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary
        {
            Key = "4",
            Category = "SK",
            Term = "Semantic Kernel",
            Definition = "Semantic Kernel is a set of libraries that allow software developers to more easily develop applications that make use of AI experiences."
        };

        yield return new Glossary
        {
            Key = "5",
            Category = "AI",
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)."
        };

        yield return new Glossary
        {
            Key = "6",
            Category = "AI",
            Term = "LLM",
            Definition = "Large language model. A type of artificial intelligence algorithm that is designed to understand and generate human language."
        };
    }
}
