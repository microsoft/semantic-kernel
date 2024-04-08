// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Search;
using Xunit;
using Xunit.Abstractions;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="AzureAITextSearchService"/>.
/// </summary>
public sealed class AzureAISearch : BaseTest
{
    /// <summary>
    /// Show how to create a <see cref="AzureAITextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create a search service with Azure AI search
        var searchService = new AzureAITextSearchService(
            endpoint: TestConfiguration.AzureAISearch.Endpoint,
            adminKey: TestConfiguration.AzureAISearch.ApiKey);

        // Create search settings for a semantic search with Azure AI search
        var searchSettings = new AzureAISearchExecutionSettings
        {
            Index = TestConfiguration.AzureAISearch.IndexName
        };

        KernelSearchResults<CustomSearchResult> searchResults = await searchService.SearchAsync<CustomSearchResult>(query, searchSettings);

        // Show using the search results
        await foreach (KernelSearchResult<CustomSearchResult> result in searchResults.Results)
        {
            WriteLine($"Title: {result.Value.Title}");
            WriteLine($"Score: {result.Metadata?["Score"]}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Value.Chunk);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    public AzureAISearch(ITestOutputHelper output) : base(output)
    {
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
