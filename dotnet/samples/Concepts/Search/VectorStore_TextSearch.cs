// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using OpenAI;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="VectorStoreTextSearch{TRecord}"/> instance.
/// </summary>
public class VectorStore_TextSearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="VectorStoreTextSearch{TRecord}"/> and use it to perform a text search
    /// on top of the <see cref="InMemoryVectorStore"/>.
    /// </summary>
    [Fact]
    public async Task UsingInMemoryVectorStoreRecordTextSearchAsync()
    {
        // Create an embedding generation service.
        var embeddingGenerator = new OpenAIClient(TestConfiguration.OpenAI.ApiKey)
            .GetEmbeddingClient(TestConfiguration.OpenAI.EmbeddingModelId)
            .AsIEmbeddingGenerator();

        // Construct an InMemory vector store.
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collectionName = "records";

        // Delegate which will create a record.
        static DataModel CreateRecord(string text)
        {
            return new()
            {
                Key = Guid.NewGuid(),
                Text = text
            };
        }

        // Create a record collection from a list of strings using the provided delegate.
        string[] lines =
        [
            "Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase. It serves as an efficient middleware that enables rapid delivery of enterprise-grade solutions.",
            "Semantic Kernel is a new AI SDK, and a simple and yet powerful programming model that lets you add large language capabilities to your app in just a matter of minutes. It uses natural language prompting to create and execute semantic kernel AI tasks across multiple languages and platforms.",
            "In this guide, you learned how to quickly get started with Semantic Kernel by building a simple AI agent that can interact with an AI service and run your code. To see more examples and learn how to build more complex AI agents, check out our in-depth samples."
        ];
        var collection = await CreateCollectionFromListAsync<Guid, DataModel>(
            vectorStore, collectionName, lines, CreateRecord);

        // Create a text search instance using the InMemory vector store.
        var textSearch = new VectorStoreTextSearch<DataModel>(collection);
        await ExecuteSearchesAsync(textSearch);

        // Create a text search instance using a vectorized search wrapper around the InMemory vector store.
        textSearch = new VectorStoreTextSearch<DataModel>(collection);
        await ExecuteSearchesAsync(textSearch);
    }

    private async Task ExecuteSearchesAsync(VectorStoreTextSearch<DataModel> textSearch)
    {
        var query = "What is the Semantic Kernel?";

        // Search and return results as a string items
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 2, Skip = 0 });
        Console.WriteLine("--- String Results ---\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 2, Skip = 0 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            WriteHorizontalRule();
        }

        // Search and returns results as DataModel items
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 2, Skip = 0 });
        Console.WriteLine("\n--- DataModel Results ---\n");
        await foreach (DataModel result in fullResults.Results)
        {
            Console.WriteLine($"Key:         {result.Key}");
            Console.WriteLine($"Text:        {result.Text}");
            Console.WriteLine($"Embedding:   {result.Embedding.Length}");
            WriteHorizontalRule();
        }
    }

    /// <summary>
    /// Delegate to create a record.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    internal delegate TRecord CreateRecord<TKey, TRecord>(string text) where TKey : notnull;

    /// <summary>
    /// Create a <see cref="VectorStoreCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Creating an instance of <see cref="InMemoryCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="VectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="entries">A list of strings.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    internal static async Task<VectorStoreCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
        VectorStore vectorStore,
        string collectionName,
        string[] entries,
        CreateRecord<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : class
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.EnsureCollectionExistsAsync().ConfigureAwait(false);

        // Generate the records and upsert them.
        var records = entries.Select(x => createRecord(x));
        await collection.UpsertAsync(records);

        return collection;
    }

    /// <summary>
    /// Sample model class that represents a record entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    private sealed class DataModel
    {
        [VectorStoreKey]
        [TextSearchResultName]
        public Guid Key { get; init; }

        [VectorStoreData]
        [TextSearchResultValue]
        public string Text { get; init; }

        [VectorStoreVector(1536)]
        public string Embedding => this.Text;
    }
}
