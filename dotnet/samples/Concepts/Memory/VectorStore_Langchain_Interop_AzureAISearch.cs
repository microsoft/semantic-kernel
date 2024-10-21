// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Azure;
using Azure.Identity;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory;

/// <summary>
/// Example showing how to consume data that had previously been
/// ingested into an Azure AI Search instance using Langchain.
/// </summary>
/// <remarks>
/// To run this sample, you need to first create an instance of an
/// Azure AI Search collection using Langhain.
/// This sample assumes that you used the pets sample data set from this article:
/// https://python.langchain.com/docs/tutorials/retrievers/#documents
/// And the from_documents method to create the collection as shown here:
/// https://python.langchain.com/docs/tutorials/retrievers/#vector-stores
/// </remarks>
public class VectorStore_Langchain_Interop_AzureAISearch(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ReadDataFromLangchainAzureAISearchAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Create a vector store.
        var searchIndexClient = new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey));
        var vectorStore = new AzureAISearchVectorStore(searchIndexClient);

        // Get the collection.
        var collection = vectorStore.GetCollection<string, AzureAISearchLangchainDocument>("pets");

        // Search the data set.
        var searchString = "I'm looking for an animal that is loyal and will make a great companion";
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        var searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Top = 1 });
        var resultRecords = await searchResult.Results.ToListAsync();

        this.Output.WriteLine("Search string: " + searchString);
        this.Output.WriteLine("Source: " + resultRecords.First().Record.Metadata);
        this.Output.WriteLine("Text: " + resultRecords.First().Record.Content);
        this.Output.WriteLine();
    }

    /// <summary>
    /// Model class that matches the storage format used by Langchain for Azure AI Search.
    /// </summary>
    private sealed class AzureAISearchLangchainDocument
    {
        [JsonPropertyName("id")]
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [JsonPropertyName("content")]
        [VectorStoreRecordData]
        public string Content { get; set; }

        /// <summary>
        /// The storage format used by Lanchain stores the source information
        /// in the metadata field as a JSON string.
        /// E.g. {"source": "my-doc"}
        /// </summary>
        [JsonPropertyName("metadata")]
        [VectorStoreRecordData]
        public string Metadata { get; set; }

        [JsonPropertyName("content_vector")]
        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
