// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace Memory;

/// <summary>
/// An example showing how to do paging when there are many records in the database and you want to page through these page by page.
///
/// The example shows the following steps:
/// 1. Create an InMemory Vector Store.
/// 2. Generate and add some test data entries.
/// 3. Read the data back using vector search by paging through the results page by page.
/// </summary>
public class VectorStore_VectorSearch_Paging(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task VectorSearchWithPagingAsync()
    {
        // Construct an InMemory vector store.
        var vectorStore = new InMemoryVectorStore();

        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<int, TextSnippet>("skglossary");
        await collection.CreateCollectionIfNotExistsAsync();

        // Create some test data entries.
        // We are not generating real embeddings here, just some random numbers
        // to keep the example simple.
        for (int i = 0; i < 1000; i++)
        {
            var text = $"This is a test text snippet {i}";
            var embedding = new ReadOnlyMemory<float>([i, i + 1, i + 2, i + 3]);
            var textSnippet = new TextSnippet { Key = i, Text = text, TextEmbedding = embedding };
            await collection.UpsertAsync(textSnippet);
        }

        // Create a vector to search with.
        // We are not generating a real embedding here, just some random numbers
        // to keep the example simple.
        var searchVector = new ReadOnlyMemory<float>([0, 1, 2, 3]);

        // Loop until there are no more results.
        var page = 0;
        var moreResults = true;
        while (moreResults)
        {
            // Get the next page of results by asking for 10 results, and using 'Skip' to skip the results from the previous pages.
            var currentPageResults = collection.SearchEmbeddingAsync(
                searchVector,
                top: 10,
                new()
                {
                    Skip = page * 10
                });

            // Print the results.
            var pageCount = 0;
            await foreach (var result in currentPageResults)
            {
                Console.WriteLine($"Key: {result.Record.Key}, Text: {result.Record.Text}");
                pageCount++;
            }

            // Stop when we got back less than the requested number of results.
            moreResults = pageCount == 10;
            page++;
        }
    }

    /// <summary>
    /// Sample model class that can store some text and its embedding.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    private sealed class TextSnippet
    {
        [VectorStoreRecordKey]
        public int Key { get; set; }

        [VectorStoreRecordData]
        public string Text { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> TextEmbedding { get; set; }
    }
}
