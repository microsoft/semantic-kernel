// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Identity;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;
using StackExchange.Redis;
using Sdk = Pinecone;

namespace Memory.VectorstoreLangchainInterop;

/// <summary>
/// Example showing how to consume data that had previously been
/// ingested into a database using Langchain.
/// </summary>
/// <remarks>
/// To run these samples, you need to first create collections instances using Langhain.
/// This sample assumes that you used the pets sample data set from this article:
/// https://python.langchain.com/docs/tutorials/retrievers/#documents
/// And the from_documents method to create the collection as shown here:
/// https://python.langchain.com/docs/tutorials/retrievers/#vector-stores
/// </remarks>
public class LangchainInterop(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ReadDataFromLangchainAzureAISearchAsync()
    {
        var searchIndexClient = new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey));
        var vectorStore = AzureAISearchFactory.CreateQdrantLangchainInteropVectorStore(searchIndexClient);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

    [Fact]
    public async Task ReadDataFromLangchainQdrantAsync()
    {
        var qdrantClient = new QdrantClient("localhost");
        var vectorStore = QdrantFactory.CreateQdrantLangchainInteropVectorStore(qdrantClient);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

    [Fact]
    public async Task ReadDataFromLangchainPineconeAsync()
    {
        var pineconeClient = new Sdk.PineconeClient(TestConfiguration.Pinecone.ApiKey);
        var vectorStore = PineconeFactory.CreatePineconeLangchainInteropVectorStore(pineconeClient);
        await this.ReadDataFromCollectionAsync(vectorStore, "pets");
    }

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
