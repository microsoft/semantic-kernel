// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Search;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="AzureAITextSearchService"/>.
/// </summary>
public sealed class AzureAISearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="AzureAITextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task SearchAsync()
    {
        var query = "What is the Semantic Kernel?";
        var IndexName = TestConfiguration.AzureAISearch.IndexName;

        // Create a search service with Azure AI search
        var searchService = new AzureAITextSearchService(
            endpoint: TestConfiguration.AzureAISearch.Endpoint,
            adminKey: TestConfiguration.AzureAISearch.ApiKey);

        // Search with a custom search result type
        KernelSearchResults<CustomSearchResult> searchResults = await searchService.SearchAsync<CustomSearchResult>(query, new() { Index = IndexName, Count = 2, Offset = 2 });
        await foreach (CustomSearchResult result in searchResults.Results)
        {
            Console.WriteLine($"Title: {result.Title}");
            Console.WriteLine($"Chunk Id: {result.ChunkId}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Chunk);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search for just the summaries
        AzureAISearchExecutionSettings settings = new() { Index = IndexName, Count = 2, Offset = 2, ValueField = "chunk" };
        KernelSearchResults<string> summaryResults = await searchService.SearchAsync<string>(query, settings);
        await foreach (string result in summaryResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult result type
        settings = new() { Index = IndexName, Count = 2, Offset = 2, NameField = "title", ValueField = "chunk", LinkField = "metadata_spo_item_weburi" };
        KernelSearchResults<TextSearchResult> textResults = await searchService.SearchAsync<TextSearchResult>(query, settings);
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Value);
            Console.WriteLine(result.Link);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<SearchDocument> fullResults = await searchService.SearchAsync<SearchDocument>(query, new() { Index = IndexName, Count = 2, Offset = 6 });
        await foreach (SearchDocument result in fullResults.Results)
        {
            Console.WriteLine($"Title: {result.GetString("title")}");
            Console.WriteLine($"Chunk Id: {result.GetString("chunk_id")}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.GetString("chunk"));
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    /// <summary>
    /// Represents a custom search result.
    /// </summary>
    public class CustomSearchResult
    {
        [JsonPropertyName("title")]
        public string? Title { get; set; }
        [JsonPropertyName("chunk_id")]
        public string? ChunkId { get; set; }
        [JsonPropertyName("chunk")]
        public string? Chunk { get; set; }
    }
}
