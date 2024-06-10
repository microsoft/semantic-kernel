// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="BingTextSearchService"/>.
/// </summary>
public sealed class BingSearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="BingTextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task SearchAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create a search service with Bing search service
        var searchService = new BingTextSearchService(
            endpoint: TestConfiguration.Bing.Endpoint,
            apiKey: TestConfiguration.Bing.ApiKey);

        // Search with a custom search result type
        KernelSearchResults<CustomSearchResult> searchResults = await searchService.SearchAsync<CustomSearchResult>(query, new() { Count = 2 });
        await foreach (CustomSearchResult result in searchResults.Results)
        {
            Console.WriteLine($"Title: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Snippet);
            Console.WriteLine(result.Url);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search for just the summaries
        KernelSearchResults<string> summaryResults = await searchService.SearchAsync<string>(query, new() { Count = 2, Offset = 2 });
        await foreach (string result in summaryResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult result type
        KernelSearchResults<TextSearchResult> textResults = await searchService.SearchAsync<TextSearchResult>(query, new() { Count = 2, Offset = 4 });
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Value);
            Console.WriteLine(result.Link);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<BingWebPage> fullResults = await searchService.SearchAsync<BingWebPage>(query, new() { Count = 2, Offset = 6 });
        await foreach (BingWebPage result in fullResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Snippet);
            Console.WriteLine(result.Url);
            Console.WriteLine(result.DisplayUrl);
            Console.WriteLine(result.DateLastCrawled);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
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
