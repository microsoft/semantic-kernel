// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace GettingStartedWithVectorStores;

/// <summary>
/// Example that shows that you can switch between different vector stores with the same code.
/// </summary>
public class Step3_Switch_VectorStore(ITestOutputHelper output, VectorStoresFixture fixture) : BaseTest(output), IClassFixture<VectorStoresFixture>
{
    /// <summary>
    /// Here we are going to use the same code that we used in <see cref="Step1_Ingest_Data"/> and <see cref="Step2_Vector_Search"/>
    /// but now with an <see cref="AzureAISearchVectorStore"/>
    ///
    /// This example requires an Azure AI Search service to be available.
    /// </summary>
    [Fact]
    public async Task UseAnAzureAISearchVectorStoreAsync()
    {
        // Construct an Azure AI Search vector store and get the collection.
        var vectorStore = new AzureAISearchVectorStore(new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey)));
        var collection = vectorStore.GetCollection<string, Glossary>("skglossary");

        // Ingest data into the collection using the same code as we used in Step1 with the InMemory Vector Store.
        await Step1_Ingest_Data.IngestDataIntoVectorStoreAsync(collection, fixture.EmbeddingGenerator);

        // Search the vector store using the same code as we used in Step2 with the InMemory Vector Store.
        var searchResultItem = await Step2_Vector_Search.SearchVectorStoreAsync(
            collection,
            "What is an Application Programming Interface?",
            fixture.EmbeddingGenerator);

        // Write the search result with its score to the console.
        Console.WriteLine(searchResultItem.Record.Definition);
        Console.WriteLine(searchResultItem.Score);
    }

    /// <summary>
    /// Here we are going to use the same code that we used in <see cref="Step1_Ingest_Data"/> and <see cref="Step2_Vector_Search"/>
    /// but now with a <see cref="RedisVectorStore"/>
    ///
    /// This example requires a Redis server running on localhost:6379. To run a Redis server in a Docker container, use the following command:
    /// docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    /// </summary>
    [Fact]
    public async Task UseARedisVectorStoreAsync()
    {
        // Construct a Redis vector store and get the collection.
        var vectorStore = new RedisVectorStore(ConnectionMultiplexer.Connect("localhost:6379").GetDatabase());
        var collection = vectorStore.GetCollection<string, Glossary>("skglossary");

        // Ingest data into the collection using the same code as we used in Step1 with the InMemory Vector Store.
        await Step1_Ingest_Data.IngestDataIntoVectorStoreAsync(collection, fixture.EmbeddingGenerator);

        // Search the vector store using the same code as we used in Step2 with the InMemory Vector Store.
        var searchResultItem = await Step2_Vector_Search.SearchVectorStoreAsync(
            collection,
            "What is an Application Programming Interface?",
            fixture.EmbeddingGenerator);

        // Write the search result with its score to the console.
        Console.WriteLine(searchResultItem.Record.Definition);
        Console.WriteLine(searchResultItem.Score);
    }
}
