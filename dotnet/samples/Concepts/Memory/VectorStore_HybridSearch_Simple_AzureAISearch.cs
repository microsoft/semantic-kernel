// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Identity;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory;

/// <summary>
/// A simple example showing how to ingest data into a vector store and then use hybrid search to find related records to a given string and set of keywords.
///
/// The example shows the following steps:
/// 1. Create an embedding generator.
/// 2. Create an AzureAISearch Vector Store.
/// 3. Ingest some data into the vector store.
/// 4. Do a hybrid search on the vector store with various text+keyword and filtering options.
/// </summary>
public class VectorStore_HybridSearch_Simple_AzureAISearch(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task IngestDataAndUseHybridSearch()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Construct the AzureAISearch VectorStore.
        var searchIndexClient = new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey));
        var vectorStore = new AzureAISearchVectorStore(searchIndexClient);

        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<string, Glossary>("skglossary");
        await collection.CreateCollectionIfNotExistsAsync();
        var hybridSearchCollection = (IKeywordHybridSearch<Glossary>)collection;

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGlossaryEntries().ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.DefinitionEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Definition);
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        var upsertedKeysTasks = glossaryEntries.Select(x => collection.UpsertAsync(x));
        var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);

        // Search the collection using a vector search.
        var searchString = "What is an Application Programming Interface";
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        var searchResult = await hybridSearchCollection.HybridSearchAsync(searchVector, ["Application", "Programming", "Interface"], new() { Top = 1 });
        var resultRecords = await searchResult.Results.ToListAsync();

        Console.WriteLine("Search string: " + searchString);
        Console.WriteLine("Result: " + resultRecords.First().Record.Definition);
        Console.WriteLine();

        // Search the collection using a vector search.
        searchString = "What is Retrieval Augmented Generation";
        searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        searchResult = await hybridSearchCollection.HybridSearchAsync(searchVector, ["Retrieval", "Augmented", "Generation"], new() { Top = 1 });
        resultRecords = await searchResult.Results.ToListAsync();

        Console.WriteLine("Search string: " + searchString);
        Console.WriteLine("Result: " + resultRecords.First().Record.Definition);
        Console.WriteLine();

        // Search the collection using a vector search with pre-filtering.
        searchString = "What is Retrieval Augmented Generation";
        searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        searchResult = await hybridSearchCollection.HybridSearchAsync(searchVector, ["Retrieval", "Augmented", "Generation"], new() { Top = 3, Filter = g => g.Category == "External Definitions" });
        resultRecords = await searchResult.Results.ToListAsync();

        Console.WriteLine("Search string: " + searchString);
        Console.WriteLine("Number of results: " + resultRecords.Count);
        Console.WriteLine("Result 1 Score: " + resultRecords[0].Score);
        Console.WriteLine("Result 1: " + resultRecords[0].Record.Definition);
        Console.WriteLine("Result 2 Score: " + resultRecords[1].Score);
        Console.WriteLine("Result 2: " + resultRecords[1].Record.Definition);
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
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData(IsFilterable = true)]
        public string Category { get; set; }

        [VectorStoreRecordData]
        public string Term { get; set; }

        [VectorStoreRecordData(IsFullTextSearchable = true)]
        public string Definition { get; set; }

        [VectorStoreRecordVector(1536)]
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
            Key = "1",
            Category = "External Definitions",
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary
        {
            Key = "2",
            Category = "Core Definitions",
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary
        {
            Key = "3",
            Category = "External Definitions",
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)."
        };
    }
}
