// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using System.Text.Json;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using Resources;

namespace Memory;

/// <summary>
/// Sample showing how to create an <see cref="InMemoryVectorStore"/> collection from a list of strings
/// and then save it to disk so that it can be reloaded later.
/// </summary>
public class InMemoryVectorStore_LoadData(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task LoadStringListAndSearchAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        var handler = new LoggingHandler(new HttpClientHandler(), this.Output);
        var httpClient = new HttpClient(handler);

        // Create an embedding generation service.
        var embeddingGenerator = new OpenAI.OpenAIClient(
            new ApiKeyCredential(TestConfiguration.OpenAI.ApiKey),
            new OpenAI.OpenAIClientOptions() { Transport = new HttpClientPipelineTransport(httpClient) })
                .GetEmbeddingClient(TestConfiguration.OpenAI.EmbeddingModelId)
                .AsIEmbeddingGenerator(1536);

        // Construct an InMemory vector store.
        var vectorStore = new InMemoryVectorStore();
        var collectionName = "records";

        // Path to the file where the record collection will be saved to and loaded from.
        string filePath = Path.Combine(Path.GetTempPath(), "semantic-kernel-info.json");
        if (!File.Exists(filePath))
        {
            // Read a list of text strings from a file, to load into a new record collection.
            var skInfo = EmbeddedResource.Read("semantic-kernel-info.txt");
            var lines = skInfo!.Split('\n');

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
            var collection = await vectorStore.CreateCollectionFromListAsync<Guid, DataModel>(
                collectionName, lines, embeddingGenerator, CreateRecord);

            // Save the record collection to a file stream.
            using (FileStream fileStream = new(filePath, FileMode.OpenOrCreate))
            {
                await vectorStore.SerializeCollectionAsJsonAsync<Guid, DataModel>(collectionName, fileStream);
            }
        }

        // Load the record collection from the file stream and perform a search.
        using (FileStream fileStream = new(filePath, FileMode.Open))
        {
            var vectorSearch = await vectorStore.DeserializeCollectionFromJsonAsync<Guid, DataModel>(fileStream);

            // Search the collection using a vector search.
            var searchString = "What is the Semantic Kernel?";
            var searchVector = (await embeddingGenerator.GenerateAsync(searchString)).Vector;
            var resultRecords = await vectorSearch!.SearchAsync(searchVector, top: 1).ToListAsync();

            Console.WriteLine("Search string: " + searchString);
            Console.WriteLine("Result: " + resultRecords.First().Record.Text);
            Console.WriteLine();
        }
    }

    [Fact]
    public async Task LoadTextSearchResultsAndSearchAsync()
    {
        // Create an embedding generation service.
        var embeddingGenerator = new OpenAI.OpenAIClient(TestConfiguration.OpenAI.ApiKey)
            .GetEmbeddingClient(TestConfiguration.OpenAI.EmbeddingModelId)
            .AsIEmbeddingGenerator(1536);

        // Construct an InMemory vector store.
        var vectorStore = new InMemoryVectorStore();
        var collectionName = "records";

        // Read a list of text strings from a file, to load into a new record collection.
        var searchResultsJson = EmbeddedResource.Read("what-is-semantic-kernel.json");
        var searchResults = JsonSerializer.Deserialize<List<TextSearchResult>>(searchResultsJson!);

        // Delegate which will create a record.
        static DataModel CreateRecord(TextSearchResult searchResult, ReadOnlyMemory<float> embedding)
        {
            return new()
            {
                Key = Guid.NewGuid(),
                Title = searchResult.Name,
                Text = searchResult.Value ?? string.Empty,
                Link = searchResult.Link,
                Embedding = embedding
            };
        }

        // Create a record collection from a list of strings using the provided delegate.
        var vectorSearch = await vectorStore.CreateCollectionFromTextSearchResultsAsync<Guid, DataModel>(
            collectionName, searchResults!, embeddingGenerator, CreateRecord);

        // Search the collection using a vector search.
        var searchString = "What is the Semantic Kernel?";
        var searchVector = (await embeddingGenerator.GenerateAsync(searchString)).Vector;
        var resultRecords = await vectorSearch!.SearchAsync(searchVector, top: 1).ToListAsync();

        Console.WriteLine("Search string: " + searchString);
        Console.WriteLine("Result: " + resultRecords.First().Record.Text);
        Console.WriteLine();
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
        public Guid Key { get; init; }

        [VectorStoreData]
        public string? Title { get; init; }

        [VectorStoreData]
        public string Text { get; init; }

        [VectorStoreData]
        public string? Link { get; init; }

        [VectorStoreVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}
