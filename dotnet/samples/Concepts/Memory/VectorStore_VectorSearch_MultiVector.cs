// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory;

/// <summary>
/// An example showing how to do vector search where there may be multiple vectors
/// stored in each record and you want to specify which vector to search on.
///
/// The example shows the following steps:
/// 1. Create an InMemory Vector Store.
/// 2. Generate and add some test data entries.
/// 3. Search for records based on a specified vector.
/// </summary>
public class VectorStore_VectorSearch_MultiVector(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task VectorSearchWithMultiVectorRecordAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Construct an InMemory vector store.
        var vectorStore = new InMemoryVectorStore();

        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<int, Product>("skproducts");
        await collection.CreateCollectionIfNotExistsAsync();

        // Create product records and generate embeddings for them.
        var productRecords = CreateProductRecords().ToList();
        var tasks = productRecords.Select(entry => Task.Run(async () =>
        {
            var descriptionEmbeddingTask = textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Description);
            var featureListEmbeddingTask = textEmbeddingGenerationService.GenerateEmbeddingAsync(string.Join("\n", entry.FeatureList));

            entry.DescriptionEmbedding = await descriptionEmbeddingTask;
            entry.FeatureListEmbedding = await featureListEmbeddingTask;
        }));
        await Task.WhenAll(tasks);

        // Upsert the product records into the collection and return their keys.
        var upsertedKeysTasks = productRecords.Select(x => collection.UpsertAsync(x));
        var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);

        // Search the store using the description embedding.
        var searchString = "I am looking for a reasonably priced coffee maker";
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        var resultRecords = await collection.SearchEmbeddingAsync(
            searchVector, top: 1, new()
            {
                VectorProperty = r => r.DescriptionEmbedding
            }).ToListAsync();

        WriteLine("Search string: " + searchString);
        WriteLine("Result: " + resultRecords.First().Record.Description);
        WriteLine("Score: " + resultRecords.First().Score);
        WriteLine();

        // Search the store using the feature list embedding.
        searchString = "I am looking for a handheld vacuum cleaner that will remove pet hair";
        searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        resultRecords = await collection.SearchEmbeddingAsync(
            searchVector,
            top: 1,
            new()
            {
                VectorProperty = r => r.FeatureListEmbedding
            }).ToListAsync();

        WriteLine("Search string: " + searchString);
        WriteLine("Result: " + resultRecords.First().Record.Description);
        WriteLine("Score: " + resultRecords.First().Score);
        WriteLine();
    }

    /// <summary>
    /// Create some sample product records.
    /// </summary>
    /// <returns>A list of sample product records.</returns>
    private static IEnumerable<Product> CreateProductRecords()
    {
        yield return new Product
        {
            Key = 1,
            Description = "Premium coffee maker that allows you to make up to 20 types of drinks with one machine.",
            FeatureList = ["Milk Frother", "Easy to use", "One button operation", "Stylish design"]
        };

        yield return new Product
        {
            Key = 2,
            Description = "Value coffee maker that gives you what you need at a good price.",
            FeatureList = ["Simple design", "Easy to clean"]
        };

        yield return new Product
        {
            Key = 3,
            Description = "Efficient vacuum cleaner",
            FeatureList = ["1000W power", "Hard floor tool", "Bagless", "Corded"]
        };

        yield return new Product
        {
            Key = 4,
            Description = "High performance handheld vacuum cleaner",
            FeatureList = ["Pet hair tool", "2000W power", "Hard floor tool", "Bagless", "Cordless"]
        };
    }

    /// <summary>
    /// Sample model class that can store product information with a description and a feature list with embeddings for both.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    private sealed class Product
    {
        [VectorStoreRecordKey]
        public int Key { get; set; }

        [VectorStoreRecordData]
        public string Description { get; set; }

        [VectorStoreRecordData]
        public List<string> FeatureList { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> DescriptionEmbedding { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> FeatureListEmbedding { get; set; }
    }
}
