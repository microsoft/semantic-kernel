// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Azure.Search.Documents.Models;
using Examples;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Search;
using Xunit;
using Xunit.Abstractions;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="AzureAITextSearchService"/>.
/// </summary>
public sealed class AzureAISearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="AzureAITextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task RunAsync()
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
            WriteLine($"Title: {result.Title}");
            WriteLine($"Chunk Id: {result.ChunkId}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Chunk);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search for just the summaries
        AzureAISearchExecutionSettings settings = new() { Index = IndexName, Count = 2, Offset = 2, SnippetField = "chunk" };
        KernelSearchResults<string> summaryResults = await searchService.SearchAsync<string>(query, settings);
        await foreach (string result in summaryResults.Results)
        {
            WriteLine(result);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<SearchDocument> fullResults = await searchService.SearchAsync<SearchDocument>(query, new() { Index = IndexName, Count = 2, Offset = 4 });
        await foreach (SearchDocument result in fullResults.Results)
        {
            WriteLine($"Title: {result.GetString("title")}");
            WriteLine($"Chunk Id: {result.GetString("chunk_id")}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.GetString("chunk"));
            WriteLine("------------------------------------------------------------------------------------------------------------------");
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
