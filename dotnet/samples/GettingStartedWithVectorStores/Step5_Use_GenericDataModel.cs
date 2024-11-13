﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Embeddings;
using StackExchange.Redis;

namespace GettingStartedWithVectorStores;

/// <summary>
/// Example that shows that you can use the generic data model to interact with a vector database.
/// This makes it possible to use the vector store abstractions without having to create your own data model.
/// </summary>
public class Step5_Use_GenericDataModel(ITestOutputHelper output, VectorStoresFixture fixture) : BaseTest(output), IClassFixture<VectorStoresFixture>
{
    /// <summary>
    /// Example showing how to query a vector store that uses the generic data model.
    ///
    /// This example requires a Redis server running on localhost:6379. To run a Redis server in a Docker container, use the following command:
    /// docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    /// </summary>
    [Fact]
    public async Task SearchAVectorStoreWithGenericDataModelAsync()
    {
        // Construct a redis vector store.
        var vectorStore = new RedisVectorStore(ConnectionMultiplexer.Connect("localhost:6379").GetDatabase());

        // First, let's use the code from step 1 to ingest data into the vector store
        // using the custom data model, simulating a scenario where someone else ingested
        // the data into the database previously.
        var collection = vectorStore.GetCollection<string, Glossary>("skglossary");
        var customDataModelCollection = vectorStore.GetCollection<string, Glossary>("skglossary");
        await Step1_Ingest_Data.IngestDataIntoVectorStoreAsync(customDataModelCollection, fixture.TextEmbeddingGenerationService);

        // To use the generic data model, we still have to describe the storage schema to the vector store
        // using a record definition. The benefit over a custom data model is that this definition
        // does not have to be known at compile time.
        // E.g. it can be read from a configuration or retrieved from a service.
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("Category", typeof(string)),
                new VectorStoreRecordDataProperty("Term", typeof(string)),
                new VectorStoreRecordDataProperty("Definition", typeof(string)),
                new VectorStoreRecordVectorProperty("DefinitionEmbedding", typeof(ReadOnlyMemory<float>)) { Dimensions = 1536 },
            }
        };

        // Now, let's create a collection that uses the generic data model.
        var genericDataModelCollection = vectorStore.GetCollection<string, VectorStoreGenericDataModel<string>>("skglossary", recordDefinition);

        // Generate an embedding from the search string.
        var searchString = "How do I provide additional context to an LLM?";
        var searchVector = await fixture.TextEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);

        // Search the generic data model collection and get the single most relevant result.
        var searchResult = await genericDataModelCollection.VectorizedSearchAsync(
            searchVector,
            new()
            {
                Top = 1,
            });
        var searchResultItems = await searchResult.Results.ToListAsync();

        // Write the search result with its score to the console.
        // Note that here we can loop through all the data properties
        // without knowing the schema, since the data properties are
        // stored as a dictionary of string keys and object values
        // when using the generic data model.
        foreach (var dataProperty in searchResultItems.First().Record.Data)
        {
            Console.WriteLine($"{dataProperty.Key}: {dataProperty.Value}");
        }
        Console.WriteLine(searchResultItems.First().Score);
    }
}
