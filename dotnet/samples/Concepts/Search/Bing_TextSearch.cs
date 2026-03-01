// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // Obsolete TextSearchOptions/TextSearchFilter

using System.Text.Json;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;

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
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 4, Skip = 0 });
        Console.WriteLine("--- String Results ---\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 4, Skip = 4 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            WriteHorizontalRule();
        }

        // Search and return s results as BingWebPage items
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 4, Skip = 8 });
        Console.WriteLine("\n--- Bing Web Page Results ---\n");
        await foreach (BingWebPage result in fullResults.Results)
        {
            Console.WriteLine($"Name:            {result.Name}");
            Console.WriteLine($"Snippet:         {result.Snippet}");
            Console.WriteLine($"Url:             {result.Url}");
            Console.WriteLine($"DisplayUrl:      {result.DisplayUrl}");
            Console.WriteLine($"DateLastCrawled: {result.DateLastCrawled}");
            WriteHorizontalRule();
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
            StringMapper = new TestTextSearchStringMapper(),
        });

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 2, Skip = 0 });
        Console.WriteLine("--- Serialized JSON Results ---");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
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
            StringMapper = new TestTextSearchStringMapper(),
        });

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality("site", "devblogs.microsoft.com") };
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, searchOptions);
        Console.WriteLine("--- Microsoft Developer Blogs Results ---");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine(result.Link);
            WriteHorizontalRule();
        }
    }

    /// <summary>
    /// Show how to use enhanced LINQ filtering with BingTextSearch for type-safe searches.
    /// </summary>
    [Fact]
    public async Task UsingBingTextSearchWithLinqFilteringAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        using HttpClient httpClient = new(handler);

        // Create an ITextSearch<BingWebPage> instance for type-safe LINQ filtering
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey, options: new() { HttpClient = httpClient });

        var query = "Semantic Kernel AI";

        // Example 1: Filter by language (English only)
        Console.WriteLine("——— Example 1: Language Filter (English) ———\n");
        var languageOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 2,
            Filter = page => page.Language == "en"
        };
        var languageResults = await textSearch.SearchAsync(query, languageOptions);
        await foreach (string result in languageResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }

        // Example 2: Filter by family-friendly content
        Console.WriteLine("\n——— Example 2: Family Friendly Filter ———\n");
        var familyFriendlyOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 2,
            Filter = page => page.IsFamilyFriendly == true
        };
        var familyFriendlyResults = await textSearch.SearchAsync(query, familyFriendlyOptions);
        await foreach (string result in familyFriendlyResults.Results)
        {
            Console.WriteLine(result);
            WriteHorizontalRule();
        }

        // Example 3: Compound AND filtering (language + family-friendly)
        Console.WriteLine("\n——— Example 3: Compound Filter (English + Family Friendly) ———\n");
        var compoundOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 2,
            Filter = page => page.Language == "en" && page.IsFamilyFriendly == true
        };
        var compoundResults = await textSearch.GetSearchResultsAsync(query, compoundOptions);
        await foreach (BingWebPage page in compoundResults.Results)
        {
            Console.WriteLine($"Name: {page.Name}");
            Console.WriteLine($"Snippet: {page.Snippet}");
            Console.WriteLine($"Language: {page.Language}");
            Console.WriteLine($"Family Friendly: {page.IsFamilyFriendly}");
            WriteHorizontalRule();
        }

        // Example 4: Complex compound filtering with nullable checks
        Console.WriteLine("\n——— Example 4: Complex Compound Filter (Language + Site + Family Friendly) ———\n");
        var complexOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 2,
            Filter = page => page.Language == "en" &&
                           page.IsFamilyFriendly == true &&
                           page.DisplayUrl != null && page.DisplayUrl.Contains("microsoft")
        };
        var complexResults = await textSearch.GetSearchResultsAsync(query, complexOptions);
        await foreach (BingWebPage page in complexResults.Results)
        {
            Console.WriteLine($"Name: {page.Name}");
            Console.WriteLine($"Display URL: {page.DisplayUrl}");
            Console.WriteLine($"Language: {page.Language}");
            Console.WriteLine($"Family Friendly: {page.IsFamilyFriendly}");
            WriteHorizontalRule();
        }
    }

    #region private
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
