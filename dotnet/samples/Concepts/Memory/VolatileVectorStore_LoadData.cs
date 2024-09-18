// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Resources;

namespace Memory;

/// <summary>
/// Sample showing how to create a <see cref="VolatileVectorStore"/> collection from a list of strings
/// and then save it to disk so that it can be reloaded later.
/// </summary>
public class VolatileVectorStore_LoadData(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task LoadRecordCollectionAndSearchAsync()
    {
        // Create an embedding generation service.
        var embeddingGenerationService = new OpenAITextEmbeddingGenerationService(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);

        // Construct a volatile vector store.
        var vectorStore = new VolatileVectorStore();
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
                collectionName, lines, embeddingGenerationService, CreateRecord);

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
            var searchVector = await embeddingGenerationService.GenerateEmbeddingAsync(searchString);
            var searchResult = await vectorSearch!.VectorizedSearchAsync(searchVector, new() { Limit = 1 }).ToListAsync();

            Console.WriteLine("Search string: " + searchString);
            Console.WriteLine("Result: " + searchResult.First().Record.Text);
            Console.WriteLine();
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
}
