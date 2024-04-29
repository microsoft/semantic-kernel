// Copyright (c) Microsoft. All rights reserved.
using System;
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

        // Search with a custom search result type
        KernelSearchResults<CustomSearchResult> searchResults = await searchService.SearchAsync<CustomSearchResult>(query, new() { Count = 2 });
        await foreach (CustomSearchResult result in searchResults.Results)
        {
            WriteLine($"Title: {result.Name}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Snippet);
            WriteLine(result.Url);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search for just the summaries
        KernelSearchResults<string> summaryResults = await searchService.SearchAsync<string>(query, new() { Count = 2, Offset = 2 });
        await foreach (string result in summaryResults.Results)
        {
            WriteLine(result);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<BingWebPage> fullResults = await searchService.SearchAsync<BingWebPage>(query, new() { Count = 2, Offset = 4 });
        await foreach (BingWebPage result in fullResults.Results)
        {
            WriteLine($"Name: {result.Name}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Snippet);
            WriteLine(result.Url);
            WriteLine(result.DisplayUrl);
            WriteLine(result.DateLastCrawled);
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
        public Uri? Url { get; set; }
        [JsonPropertyName("snippet")]
        public string? Snippet { get; set; }
    }
}
