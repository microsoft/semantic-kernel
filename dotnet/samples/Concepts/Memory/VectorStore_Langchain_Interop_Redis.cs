// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Embeddings;
using StackExchange.Redis;

namespace Memory;

/// <summary>
/// Example showing how to consume data that had previously been
/// ingested into a Redis instance using Langchain.
/// </summary>
/// <remarks>
/// To run this sample, you need to first create an instance of a
/// Redis collection using Langhain.
/// This sample assumes that you used the pets sample data set from this article:
/// https://python.langchain.com/docs/tutorials/retrievers/#documents
/// And the from_documents method to create the collection as shown here:
/// https://python.langchain.com/docs/tutorials/retrievers/#vector-stores
/// </remarks>
public class VectorStore_Langchain_Interop_Redis(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ReadDataFromLangchainRedisAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            new AzureCliCredential());

        // Create a vector store.
        var database = ConnectionMultiplexer.Connect("localhost:6379").GetDatabase();
        var vectorStore = new RedisVectorStore(database, new() { StorageType = RedisStorageType.HashSet });

        // Get the collection.
        var collection = vectorStore.GetCollection<string, RedisLangchainDocument>("pets");

        // Search the data set.
        var searchString = "I'm looking for an animal that is loyal and will make a great companion";
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        var searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Top = 1 });
        var resultRecords = await searchResult.Results.ToListAsync();

        this.Output.WriteLine("Search string: " + searchString);
        this.Output.WriteLine("Source: " + resultRecords.First().Record.Source);
        this.Output.WriteLine("Text: " + resultRecords.First().Record.Content);
        this.Output.WriteLine();
    }

    /// <summary>
    /// Model class that matches the storage format used by Langchain for Redis.
    /// </summary>
    private sealed class RedisLangchainDocument
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "text")]
        public string Content { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "source")]
        public string Source { get; set; }

        [VectorStoreRecordVector(1536, StoragePropertyName = "embedding")]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
