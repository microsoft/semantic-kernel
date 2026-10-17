// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Keenable;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="KeenableTextSearch"/>.
/// Keenable works without an API key: leave the "Keenable:ApiKey" setting unset and the public endpoint is used.
/// A key lifts the per-IP rate limits of the public endpoint and is otherwise optional.
/// </summary>
public class Keenable_TextSearch(ITestOutputHelper output) : BaseTest(output)
{
#pragma warning disable CS0618 // Suppress obsolete warnings for legacy TextSearchOptions/TextSearchFilter usage
    /// <summary>
    /// Show how to create a <see cref="KeenableTextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingKeenableTextSearch()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch instance using Keenable search. The API key is optional.
        var textSearch = new KeenableTextSearch(apiKey: GetApiKey(), options: new() { HttpClient = httpClient });

        var query = "What is the Semantic Kernel?";

        // Search and return results as a string items
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 4 });
        Console.WriteLine("--- String Results ---\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 4 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            WriteHorizontalRule();
        }

        // Search and return results as KeenableSearchResult items
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 4 });
        Console.WriteLine("\n--- Keenable Search Results ---\n");
        await foreach (KeenableSearchResult result in fullResults.Results)
        {
            Console.WriteLine($"Title:           {result.Title}");
            Console.WriteLine($"Snippet:         {result.Snippet}");
            Console.WriteLine($"Url:             {result.Url}");
            Console.WriteLine($"PublishedAt:     {result.PublishedAt}");
            WriteHorizontalRule();
        }
    }

    /// <summary>
    /// Show how to create a <see cref="KeenableTextSearch"/> with a shorter snippet length and a custom string mapper.
    /// </summary>
    [Fact]
    public async Task UsingKeenableTextSearchWithACustomMapper()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(apiKey: GetApiKey(), options: new()
        {
            HttpClient = httpClient,
            SnippetMaxLength = 300,
            StringMapper = new TestTextSearchStringMapper(),
        });

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 2 });
        Console.WriteLine("--- Serialized Results ---\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }
    }

    /// <summary>
    /// Show how to create a <see cref="KeenableTextSearch"/> and use it to perform a search restricted to a single site.
    /// </summary>
    [Fact]
    public async Task UsingKeenableTextSearchWithASiteFilter()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(apiKey: GetApiKey(), options: new() { HttpClient = httpClient });

        var query = "What is the Semantic Kernel?";

        // Search with a site filter and a publication date floor
        TextSearchOptions searchOptions = new()
        {
            Top = 4,
            Filter = new TextSearchFilter().Equality("site", "learn.microsoft.com").Equality("published_after", "2025-01-01")
        };
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, searchOptions);
        Console.WriteLine("--- Microsoft Learn Results ---");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine(result.Link);
            WriteHorizontalRule();
        }
    }
#pragma warning restore CS0618

    /// <summary>
    /// Show how to use LINQ filtering with KeenableTextSearch for type-safe searches.
    /// </summary>
    [Fact]
    public async Task UsingKeenableTextSearchWithLinqFilteringAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch<KeenableWebPage> instance for type-safe LINQ filtering
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(apiKey: GetApiKey(), options: new() { HttpClient = httpClient });

        var query = "Semantic Kernel AI";

        // Example 1: Restrict results to a site
        Console.WriteLine("--- Example 1: Site Filter ---\n");
        var siteOptions = new TextSearchOptions<KeenableWebPage>
        {
            Top = 2,
            Filter = page => page.Site == "learn.microsoft.com"
        };
        var siteResults = await textSearch.SearchAsync(query, siteOptions);
        await foreach (string result in siteResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }

        // Example 2: Compound AND filter, a site restriction combined with a publication date floor
        Console.WriteLine("\n--- Example 2: Site + Published After ---\n");
        var compoundOptions = new TextSearchOptions<KeenableWebPage>
        {
            Top = 2,
            Filter = page => page.Site == "github.com" && page.PublishedAfter == "2025-01-01"
        };
        var compoundResults = await textSearch.GetSearchResultsAsync(query, compoundOptions);
        await foreach (KeenableWebPage page in compoundResults.Results)
        {
            Console.WriteLine($"Title:       {page.Title}");
            Console.WriteLine($"Snippet:     {page.Snippet}");
            Console.WriteLine($"URL:         {page.Url}");
            Console.WriteLine($"PublishedAt: {page.PublishedAt}");
            WriteHorizontalRule();
        }
    }

    #region private
    /// <summary>
    /// Read the optional API key. When the "Keenable" configuration section is absent the public endpoint is used.
    /// </summary>
    private static string? GetApiKey()
    {
        try
        {
            return TestConfiguration.Keenable.ApiKey;
        }
        catch (ConfigurationNotFoundException)
        {
            return null;
        }
    }

    /// <summary>
    /// Test mapper which converts an arbitrary search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            return JsonSerializer.Serialize(result);
        }
    }
    #endregion
}
