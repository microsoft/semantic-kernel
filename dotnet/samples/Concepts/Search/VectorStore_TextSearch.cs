// Copyright (c) Microsoft. All rights reserved.

#if DISABLED

using System.Runtime.CompilerServices;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

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
        var textEmbeddingGeneration = new OpenAITextEmbeddingGenerationService(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);

        // Construct an InMemory vector store.
        var vectorStore = new InMemoryVectorStore();
        var collectionName = "records";

        // Delegate which will create a record.
        static DataModel CreateRecord(string text, ReadOnlyMemory<float> embedding)
        {
            return new()
            {
                Key = Guid.NewGuid(),
                Text = text,
                Embedding = embedding
            };
        }

        // Create a record collection from a list of strings using the provided delegate.
        string[] lines =
        [
            "Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase. It serves as an efficient middleware that enables rapid delivery of enterprise-grade solutions.",
            "Semantic Kernel is a new AI SDK, and a simple and yet powerful programming model that lets you add large language capabilities to your app in just a matter of minutes. It uses natural language prompting to create and execute semantic kernel AI tasks across multiple languages and platforms.",
            "In this guide, you learned how to quickly get started with Semantic Kernel by building a simple AI agent that can interact with an AI service and run your code. To see more examples and learn how to build more complex AI agents, check out our in-depth samples."
        ];
        var vectorizedSearch = await CreateCollectionFromListAsync<Guid, DataModel>(
            vectorStore, collectionName, lines, textEmbeddingGeneration, CreateRecord);

        // Create a text search instance using the InMemory vector store.
        var textSearch = new VectorStoreTextSearch<DataModel>(vectorizedSearch, textEmbeddingGeneration);
        await ExecuteSearchesAsync(textSearch);

        // Create a text search instance using a vectorized search wrapper around the InMemory vector store.
        IVectorizableTextSearch<DataModel> vectorizableTextSearch = new VectorizedSearchWrapper<DataModel>(vectorizedSearch, textEmbeddingGeneration);
        textSearch = new VectorStoreTextSearch<DataModel>(vectorizableTextSearch);
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
    internal delegate TRecord CreateRecord<TKey, TRecord>(string text, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Create a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Creating an instance of <see cref="InMemoryVectorStoreRecordCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="IVectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="entries">A list of strings.</param>
    /// <param name="embeddingGenerationService">A text embedding generation service.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    internal static async Task<IVectorStoreRecordCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
        IVectorStore vectorStore,
        string collectionName,
        string[] entries,
        ITextEmbeddingGenerationService embeddingGenerationService,
        CreateRecord<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : notnull
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.CreateCollectionIfNotExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = entries.Select(entry => Task.Run(async () =>
        {
            var record = createRecord(entry, await embeddingGenerationService.GenerateEmbeddingAsync(entry).ConfigureAwait(false));
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }

    /// <summary>
    /// Decorator for a <see cref="IVectorSearch{TRecord}"/> that generates embeddings for text search queries.
    /// </summary>
    private sealed class VectorizedSearchWrapper<TRecord>(IVectorSearch<TRecord> vectorizedSearch, ITextEmbeddingGenerationService textEmbeddingGeneration) : IVectorizableTextSearch<TRecord>
    {
        /// <inheritdoc/>
        public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizableTextSearchAsync(string searchText, int top, VectorSearchOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            var vectorizedQuery = await textEmbeddingGeneration!.GenerateEmbeddingAsync(searchText, cancellationToken: cancellationToken).ConfigureAwait(false);

            await foreach (var result in vectorizedSearch.VectorizedSearchAsync(vectorizedQuery, top, options, cancellationToken))
            {
                yield return result;
            }
        }

        /// <inheritdoc />
        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            ArgumentNullException.ThrowIfNull(serviceType);

            return
                serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
                vectorizedSearch.GetService(serviceType, serviceKey);
        }
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
        [VectorStoreRecordKey]
        [TextSearchResultName]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        [TextSearchResultValue]
        public string Text { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}

#endif
