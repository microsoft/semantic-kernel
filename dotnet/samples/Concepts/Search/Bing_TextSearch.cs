// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="BingTextSearch"/>.
/// </summary>
public class Bing_TextSearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingBingTextSearchAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey, options: new() { HttpClient = httpClient });

        var query = "What is the Semantic Kernel?";

        // Search and return results as a string items
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Count = 4, Offset = 0 });
        Console.WriteLine("--- String Results ---\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Count = 4, Offset = 4 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }

        // Search and return s results as BingWebPage items
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Count = 4, Offset = 8 });
        Console.WriteLine("\n--- Bing Web Page Results ---\n");
        await foreach (BingWebPage result in fullResults.Results)
        {
            Console.WriteLine($"Name:            {result.Name}");
            Console.WriteLine($"Snippet:         {result.Snippet}");
            Console.WriteLine($"Url:             {result.Url}");
            Console.WriteLine($"DisplayUrl:      {result.DisplayUrl}");
            Console.WriteLine($"DateLastCrawled: {result.DateLastCrawled}");
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingBingTextSearchWithACustomMapperAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey, options: new()
        {
            HttpClient = httpClient,
            MapToString = webPage => JsonSerializer.Serialize(webPage),
        });

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Count = 2, Offset = 0 });
        Console.WriteLine("--- Serialized JSON Results ---");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingBingTextSearchWithASiteFilterAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey, options: new()
        {
            HttpClient = httpClient,
            MapToString = webPage => JsonSerializer.Serialize(webPage),
        });

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        TextSearchOptions searchOptions = new() { Count = 4, Offset = 0, BasicFilter = new BasicFilterOptions().Equality("site", "devblogs.microsoft.com") };
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, searchOptions);
        Console.WriteLine("--- Microsoft Developer Blogs Results ---");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine(result.Link);
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }
    }

    #region private
    private const int HorizontalRuleLength = 80;
    #endregion
}
