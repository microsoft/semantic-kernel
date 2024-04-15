// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;
using Xunit;
using Xunit.Abstractions;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="ITextSearchService"/>.
/// </summary>
public sealed class BingSearch : BaseTest
{
    /// <summary>
    /// Show how to create a <see cref="BingTextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create a search service with Azure AI search
        var searchService = new BingTextSearchService(
            endpoint: TestConfiguration.Bing.Endpoint,
            apiKey: TestConfiguration.Bing.ApiKey);

        // Create search settings for a semantic search with Bing search
        var searchSettings = new SearchExecutionSettings
        {
        };

        KernelSearchResults<CustomSearchResult> searchResults = await searchService.SearchAsync<CustomSearchResult>(query, searchSettings);

        // Show using the search results
        await foreach (KernelSearchResult<CustomSearchResult> result in searchResults.Results)
        {
            WriteLine($"Title: {result.Value.Name}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Value.Snippet);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    public BingSearch(ITestOutputHelper output) : base(output)
    {
    }

    /// <summary>
    /// Represents a custom search result.
    /// </summary>
    public class CustomSearchResult
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }
        [JsonPropertyName("url")]
        public string? Url { get; set; }
        [JsonPropertyName("snippet")]
        public string? Snippet { get; set; }
    }
}
