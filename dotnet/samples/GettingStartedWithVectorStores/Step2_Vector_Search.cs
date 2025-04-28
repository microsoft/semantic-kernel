// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;

namespace GettingStartedWithVectorStores;

/// <summary>
/// Example showing how to do vector searches with an in-memory vector store.
/// </summary>
public class Step2_Vector_Search(ITestOutputHelper output, VectorStoresFixture fixture) : BaseTest(output), IClassFixture<VectorStoresFixture>
{
    /// <summary>
    /// Do a basic vector search where we just want to retrieve the single most relevant result.
    /// </summary>
    [Fact]
    public async Task SearchAnInMemoryVectorStoreAsync()
    {
        var collection = await GetVectorStoreCollectionWithDataAsync();

        // Search the vector store.
        var searchResultItem = await SearchVectorStoreAsync(
            collection,
            "What is an Application Programming Interface?",
            fixture.TextEmbeddingGenerationService);

        // Write the search result with its score to the console.
        Console.WriteLine(searchResultItem.Record.Definition);
        Console.WriteLine(searchResultItem.Score);
    }

    /// <summary>
    /// Search the given collection for the most relevant result to the given search string.
    /// </summary>
    /// <param name="collection">The collection to search.</param>
    /// <param name="searchString">The string to search matches for.</param>
    /// <param name="textEmbeddingGenerationService">The service to generate embeddings with.</param>
    /// <returns>The top search result.</returns>
    internal static async Task<VectorSearchResult<Glossary>> SearchVectorStoreAsync(IVectorStoreRecordCollection<string, Glossary> collection, string searchString, ITextEmbeddingGenerationService textEmbeddingGenerationService)
    {
        // Generate an embedding from the search string.
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);

        // Search the store and get the single most relevant result.
        var searchResultItems = await collection.SearchEmbeddingAsync(
            searchVector,
            top: 1).ToListAsync();
        return searchResultItems.First();
    }

    /// <summary>
    /// Do a more complex vector search with pre-filtering.
    /// </summary>
    [Fact]
    public async Task SearchAnInMemoryVectorStoreWithFilteringAsync()
    {
        var collection = await GetVectorStoreCollectionWithDataAsync();

        // Generate an embedding from the search string.
        var searchString = "How do I provide additional context to an LLM?";
        var searchVector = await fixture.TextEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);

        // Search the store with a filter and get the single most relevant result.
        var searchResultItems = await collection.SearchEmbeddingAsync(
            searchVector,
            top: 1,
            new()
            {
                Filter = g => g.Category == "AI"
            }).ToListAsync();

        // Write the search result with its score to the console.
        Console.WriteLine(searchResultItems.First().Record.Definition);
        Console.WriteLine(searchResultItems.First().Score);
    }

    private async Task<IVectorStoreRecordCollection<string, Glossary>> GetVectorStoreCollectionWithDataAsync()
    {
        // Construct the vector store and get the collection.
        var vectorStore = new InMemoryVectorStore();
        var collection = vectorStore.GetCollection<string, Glossary>("skglossary");

        // Ingest data into the collection using the code from step 1.
        await Step1_Ingest_Data.IngestDataIntoVectorStoreAsync(collection, fixture.TextEmbeddingGenerationService);

        return collection;
    }
}
