// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Identity;
using Azure.Search.Documents.Indexes;
using Memory.VectorStoreLangchainInterop;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;
using StackExchange.Redis;
using Sdk = Pinecone;

namespace Memory;

/// <summary>
/// Example showing how to consume data that had previously been ingested into a database using Langchain.
/// The example also demonstrates how to get all vector stores to share the same data model, so where necessary
/// a conversion is done, specifically for ids, where the database requires GUIDs, but we want to use strings
/// containing GUIDs in the common data model.
/// </summary>
/// <remarks>
/// To run these samples, you need to first create collections instances using Langhain.
/// This sample assumes that you used the pets sample data set from this article:
/// https://python.langchain.com/docs/tutorials/retrievers/#documents
/// And the from_documents method to create the collection as shown here:
/// https://python.langchain.com/docs/tutorials/retrievers/#vector-stores
/// </remarks>
public class VectorStore_Langchain_Interop(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to read data from an Azure AI Search collection that was created and ingested using Langchain.
    /// </summary>
    [Fact]
    public async Task ReadDataFromLangchainAzureAISearchAsync()
    {
        var searchIndexClient = new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey));
        var vectorStore = AzureAISearchFactory.CreateQdrantLangchainInteropVectorStore(searchIndexClient);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

    /// <summary>
    /// Shows how to read data from a Qdrant collection that was created and ingested using Langchain.
    /// Also adds a converter to expose keys as strings containing GUIDs instead of <see cref="Guid"/> objects,
    /// to match the document schema of the other vector stores.
    /// </summary>
    [Fact]
    public async Task ReadDataFromLangchainQdrantAsync()
    {
        var qdrantClient = new QdrantClient("localhost");
        var vectorStore = QdrantFactory.CreateQdrantLangchainInteropVectorStore(qdrantClient);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

    /// <summary>
    /// Shows how to read data from a Pinecone collection that was created and ingested using Langchain.
    /// </summary>
    [Fact]
    public async Task ReadDataFromLangchainPineconeAsync()
    {
        var pineconeClient = new Sdk.PineconeClient(TestConfiguration.Pinecone.ApiKey);
        var vectorStore = PineconeFactory.CreatePineconeLangchainInteropVectorStore(pineconeClient);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

    /// <summary>
    /// Shows how to read data from a Redis collection that was created and ingested using Langchain.
    /// </summary>
    [Fact]
    public async Task ReadDataFromLangchainRedisAsync()
    {
        var database = ConnectionMultiplexer.Connect("localhost:6379").GetDatabase();
        var vectorStore = RedisFactory.CreateRedisLangchainInteropVectorStore(database);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

    /// <summary>
    /// Method to do a vector search on a collection in the provided vector store.
    /// </summary>
    /// <param name="vectorStore">The vector store to search.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <returns>An async task.</returns>
    private async Task ReadDataFromCollectionAsync(IVectorStore vectorStore, string collectionName)
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Get the collection.
        var collection = vectorStore.GetCollection<string, LangchainDocument<string>>(collectionName);

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
}
