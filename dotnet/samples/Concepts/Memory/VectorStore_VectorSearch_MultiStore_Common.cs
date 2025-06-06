// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Memory;

/// <summary>
/// This class is part of an example that shows how to ingest data into a vector store and then use vector search to find related records to a given string.
/// The example shows how to write code that can be used with multiple database types.
/// This class contains the common code.
///
/// For the entry point of the example for each database, see the following classes:
/// <para><see cref="VectorStore_VectorSearch_MultiStore_AzureAISearch"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Qdrant"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Redis"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_InMemory"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Postgres"/></para>
/// </summary>
/// <param name="vectorStore">The vector store to ingest data into.</param>
/// <param name="embeddingGenerator">The service to use for generating embeddings.</param>
/// <param name="output">A helper to write output to the xUnit test output stream.</param>
public class VectorStore_VectorSearch_MultiStore_Common(VectorStore vectorStore, IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator, ITestOutputHelper output)
{
    /// <summary>
    /// Ingest data into a collection with the given name, and search over that data.
    /// </summary>
    /// <typeparam name="TKey">The type of key to use for database records.</typeparam>
    /// <param name="collectionName">The name of the collection to ingest the data into.</param>
    /// <param name="uniqueKeyGenerator">A function to generate unique keys for each record to upsert.</param>
    /// <returns>An async task.</returns>
    public async Task IngestDataAndSearchAsync<TKey>(string collectionName, Func<TKey> uniqueKeyGenerator)
        where TKey : notnull
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, Glossary<TKey>>(collectionName);
        await collection.EnsureCollectionExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGlossaryEntries(uniqueKeyGenerator).ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.DefinitionEmbedding = (await embeddingGenerator.GenerateAsync(entry.Definition)).Vector;
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection.
        await collection.UpsertAsync(glossaryEntries);

        await Task.Delay(5000); // Add a wait to ensure that indexing completes before we continue.

        // Search the collection using a vector search.
        var searchString = "What is an Application Programming Interface";
        var searchVector = (await embeddingGenerator.GenerateAsync(searchString)).Vector;
        var resultRecords = await collection.SearchAsync(searchVector, top: 1).ToListAsync();

        output.WriteLine("Search string: " + searchString);
        output.WriteLine("Result: " + resultRecords.First().Record.Definition);
        output.WriteLine();

        // Search the collection using a vector search.
        searchString = "What is Retrieval Augmented Generation";
        searchVector = (await embeddingGenerator.GenerateAsync(searchString)).Vector;
        resultRecords = await collection.SearchAsync(searchVector, top: 1).ToListAsync();

        output.WriteLine("Search string: " + searchString);
        output.WriteLine("Result: " + resultRecords.First().Record.Definition);
        output.WriteLine();

        // Search the collection using a vector search with pre-filtering.
        searchString = "What is Retrieval Augmented Generation";
        searchVector = (await embeddingGenerator.GenerateAsync(searchString)).Vector;
        resultRecords = await collection.SearchAsync(searchVector, top: 3, new() { Filter = g => g.Category == "External Definitions" }).ToListAsync();

        output.WriteLine("Search string: " + searchString);
        output.WriteLine("Number of results: " + resultRecords.Count);
        output.WriteLine("Result 1 Score: " + resultRecords[0].Score);
        output.WriteLine("Result 1: " + resultRecords[0].Record.Definition);
        output.WriteLine("Result 2 Score: " + resultRecords[1].Score);
        output.WriteLine("Result 2: " + resultRecords[1].Record.Definition);
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
            Category = "External Definitions",
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary<TKey>
        {
            Key = uniqueKeyGenerator(),
            Category = "Core Definitions",
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary<TKey>
        {
            Key = uniqueKeyGenerator(),
            Category = "External Definitions",
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
        [VectorStoreKey]
        public TKey Key { get; set; }

        [VectorStoreData(IsIndexed = true)]
        public string Category { get; set; }

        [VectorStoreData]
        public string Term { get; set; }

        [VectorStoreData]
        public string Definition { get; set; }

        [VectorStoreVector(1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }
}
