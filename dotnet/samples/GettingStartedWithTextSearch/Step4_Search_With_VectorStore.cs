// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace GettingStartedWithTextSearch;

/// <summary>
/// This example shows how to create a <see cref="ITextSearch"/> from a
/// <see cref="IVectorStore"/>.
/// </summary>
public class Step4_Search_With_VectorStore(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="VectorStoreTextSearch{TRecord}"/> and use it to perform a search.
    /// </summary>
    [Fact]
    public async Task UsingVolatileVectorStoreRecordTextSearchAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGeneration = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Construct the Volatile VectorStore.
        var vectorStore = new VolatileVectorStore();
        var vectorizedSearch = await InitializeRecordCollectionAsync(vectorStore, textEmbeddingGeneration, "records");

        // Create a text search instance using the volatile vector store.
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var textSearch = new VectorStoreTextSearch<DataModel>(vectorizedSearch, textEmbeddingGeneration, stringMapper, resultMapper);

        // Search and return results as TextSearchResult items
        var query = "What is the Semantic Kernel?";
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 2, Skip = 0 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            WriteHorizontalRule();
        }
    }

    #region private
    /// <summary>
    /// Initialize a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with a list of strings.
    /// </summary>
    private async Task<IVectorStoreRecordCollection<Guid, DataModel>> InitializeRecordCollectionAsync(
        VolatileVectorStore vectorStore,
        ITextEmbeddingGenerationService embeddingGenerationService,
        string collectionName)
    {
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
            vectorStore, collectionName, lines, embeddingGenerationService, CreateRecord);
        return vectorizedSearch;
    }

    /// <summary>
    /// Delegate to create a record.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    internal delegate TRecord CreateRecord<TKey, TRecord>(string text, ReadOnlyMemory<float> vector) where TKey : notnull where TRecord : class;

    /// <summary>
    /// Create a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Creating an instance of <see cref="VolatileVectorStoreRecordCollection{TKey, TRecord}"/>
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
        where TRecord : class
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
    /// String mapper which converts a DataModel to a string.
    /// </summary>
    private sealed class DataModelTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is DataModel dataModel)
            {
                return dataModel.Text;
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Result mapper which converts a DataModel to a TextSearchResult.
    /// </summary>
    private sealed class DataModelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is DataModel dataModel)
            {
                return new TextSearchResult(value: dataModel.Text) { Name = dataModel.Key.ToString() };
            }
            throw new ArgumentException("Invalid result type.");
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
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        public string Text { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
    #endregion
}
