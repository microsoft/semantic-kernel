// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;

namespace Search;

public class AzureAISearchPlugin(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to register Azure AI Search service as a plugin and work with custom index schema.
    /// </summary>
    [Fact]
    public async Task AzureAISearchPluginAsync()
    {
        // Azure AI Search configuration
        Uri endpoint = new(TestConfiguration.AzureAISearch.Endpoint);
        AzureKeyCredential keyCredential = new(TestConfiguration.AzureAISearch.ApiKey);

        // Create kernel builder
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        // SearchIndexClient from Azure .NET SDK to perform search operations.
        kernelBuilder.Services.AddSingleton<SearchIndexClient>((_) => new SearchIndexClient(endpoint, keyCredential));

        // Custom AzureAISearchService to configure request parameters and make a request.
        kernelBuilder.Services.AddSingleton<IAzureAISearchService, AzureAISearchService>();

        // Embedding generation service to convert string query to vector
        kernelBuilder.AddOpenAITextEmbeddingGeneration("text-embedding-ada-002", TestConfiguration.OpenAI.ApiKey);

        // Chat completion service to ask questions based on data from Azure AI Search index.
        kernelBuilder.AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey);

        // Register Azure AI Search Plugin
        kernelBuilder.Plugins.AddFromType<MyAzureAISearchPlugin>();

        // Create kernel
        var kernel = kernelBuilder.Build();

        // Query with index name
        // The final prompt will look like this "Emily and David are...(more text based on data). Who is David?".
        var result1 = await kernel.InvokePromptAsync(
            "{{search 'David' collection='index-1'}} Who is David?");

        Console.WriteLine(result1);

        // Query with index name and search fields.
        // Search fields are optional. Since one index may contain multiple searchable fields,
        // it's possible to specify which fields should be used during search for each request.
        var arguments = new KernelArguments { ["searchFields"] = JsonSerializer.Serialize(new List<string> { "vector" }) };

        // The final prompt will look like this "Elara is...(more text based on data). Who is Elara?".
        var result2 = await kernel.InvokePromptAsync(
            "{{search 'Story' collection='index-2' searchFields=$searchFields}} Who is Elara?",
            arguments);

        Console.WriteLine(result2);
    }

    #region Index Schema

    /// <summary>
    /// Custom index schema. It may contain any fields that exist in search index.
    /// </summary>
    private sealed class IndexSchema
    {
        [JsonPropertyName("chunk_id")]
        public string ChunkId { get; set; }

        [JsonPropertyName("parent_id")]
        public string ParentId { get; set; }

        [JsonPropertyName("chunk")]
        public string Chunk { get; set; }

        [JsonPropertyName("title")]
        public string Title { get; set; }

        [JsonPropertyName("vector")]
        public ReadOnlyMemory<float> Vector { get; set; }
    }

    #endregion

    #region Azure AI Search Service

    /// <summary>
    /// Abstraction for Azure AI Search service.
    /// </summary>
    private interface IAzureAISearchService
    {
        Task<string?> SearchAsync(
            string collectionName,
            ReadOnlyMemory<float> vector,
            List<string>? searchFields = null,
            CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Implementation of Azure AI Search service.
    /// </summary>
    private sealed class AzureAISearchService(SearchIndexClient indexClient) : IAzureAISearchService
    {
        private readonly List<string> _defaultVectorFields = ["vector"];

        private readonly SearchIndexClient _indexClient = indexClient;

        public async Task<string?> SearchAsync(
            string collectionName,
            ReadOnlyMemory<float> vector,
            List<string>? searchFields = null,
            CancellationToken cancellationToken = default)
        {
            // Get client for search operations
            SearchClient searchClient = this._indexClient.GetSearchClient(collectionName);

            // Use search fields passed from Plugin or default fields configured in this class.
            List<string> fields = searchFields is { Count: > 0 } ? searchFields : this._defaultVectorFields;

            // Configure request parameters
            VectorizedQuery vectorQuery = new(vector);
            fields.ForEach(vectorQuery.Fields.Add);

            SearchOptions searchOptions = new() { VectorSearch = new() { Queries = { vectorQuery } } };

            // Perform search request
            Response<SearchResults<IndexSchema>> response = await searchClient.SearchAsync<IndexSchema>(searchOptions, cancellationToken);

            List<IndexSchema> results = [];

            // Collect search results
            await foreach (SearchResult<IndexSchema> result in response.Value.GetResultsAsync())
            {
                results.Add(result.Document);
            }

            // Return text from first result.
            // In real applications, the logic can check document score, sort and return top N results
            // or aggregate all results in one text.
            // The logic and decision which text data to return should be based on business scenario. 
            return results.FirstOrDefault()?.Chunk;
        }
    }

    #endregion

    #region Azure AI Search SK Plugin

    /// <summary>
    /// Azure AI Search SK Plugin.
    /// It uses <see cref="ITextEmbeddingGenerationService"/> to convert string query to vector.
    /// It uses <see cref="IAzureAISearchService"/> to perform a request to Azure AI Search.
    /// </summary>
    private sealed class MyAzureAISearchPlugin(
        ITextEmbeddingGenerationService textEmbeddingGenerationService,
        AzureAISearchPlugin.IAzureAISearchService searchService)
    {
        private readonly ITextEmbeddingGenerationService _textEmbeddingGenerationService = textEmbeddingGenerationService;
        private readonly IAzureAISearchService _searchService = searchService;

        [KernelFunction("Search")]
        public async Task<string> SearchAsync(
            string query,
            string collection,
            List<string>? searchFields = null,
            CancellationToken cancellationToken = default)
        {
            // Convert string query to vector
            ReadOnlyMemory<float> embedding = await this._textEmbeddingGenerationService.GenerateEmbeddingAsync(query, cancellationToken: cancellationToken);

            // Perform search
            return await this._searchService.SearchAsync(collection, embedding, searchFields, cancellationToken) ?? string.Empty;
        }
    }

    #endregion
}
