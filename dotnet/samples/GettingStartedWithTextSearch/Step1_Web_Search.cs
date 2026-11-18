// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete - Sample demonstrates legacy interface usage

using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Plugins.Web.Google;

namespace GettingStartedWithTextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="ITextSearch"/>.
/// </summary>
public class Step1_Web_Search(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> and use it to perform a search.
    /// </summary>
    [Fact]
    public async Task BingSearchAsync()
    {
        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);

        var query = "What is the Semantic Kernel?";

        // Search and return results
        KernelSearchResults<string> searchResults = await textSearch.SearchAsync(query, new TextSearchOptions { Top = 4 });
        await foreach (string result in searchResults.Results)
        {
            Console.WriteLine(result);
        }
    }

    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearch"/> and use it to perform a search.
    /// </summary>
    [Fact]
    public async Task GoogleSearchAsync()
    {
        // Create an ITextSearch instance using Google search
        var textSearch = new GoogleTextSearch(
            searchEngineId: TestConfiguration.Google.SearchEngineId,
            apiKey: TestConfiguration.Google.ApiKey);

        var query = "What is the Semantic Kernel?";

        // Search and return results
        KernelSearchResults<string> searchResults = await textSearch.SearchAsync(query, new TextSearchOptions { Top = 4 });
        await foreach (string result in searchResults.Results)
        {
            Console.WriteLine(result);
        }
    }

    /// <summary>
    /// Show how to use <see cref="BingTextSearch"/> with the new generic <see cref="ITextSearch{TRecord}"/>
    /// interface and LINQ filtering for type-safe searches.
    /// </summary>
    [Fact]
    public async Task BingSearchWithLinqFilteringAsync()
    {
#pragma warning disable CA1859 // Use concrete types when possible for improved performance - Sample intentionally demonstrates interface usage
        // Create an ITextSearch<BingWebPage> instance for type-safe LINQ filtering
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);
#pragma warning restore CA1859

        var query = "What is the Semantic Kernel?";

        // Use LINQ filtering for type-safe search with compile-time validation
        var options = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Filter = page => page.Language == "en" && page.IsFamilyFriendly == true
        };

        // Search and return strongly-typed results
        Console.WriteLine("\n--- Bing Search with LINQ Filtering ---\n");
        KernelSearchResults<BingWebPage> searchResults = await textSearch.GetSearchResultsAsync(query, options);
        await foreach (BingWebPage page in searchResults.Results)
        {
            Console.WriteLine($"Name: {page.Name}");
            Console.WriteLine($"Snippet: {page.Snippet}");
            Console.WriteLine($"Url: {page.Url}");
            Console.WriteLine($"Language: {page.Language}");
            Console.WriteLine($"Family Friendly: {page.IsFamilyFriendly}");
            Console.WriteLine("---");
        }
    }

    /// <summary>
    /// Show how to use <see cref="GoogleTextSearch"/> with the new generic <see cref="ITextSearch{TRecord}"/>
    /// interface and LINQ filtering for type-safe searches.
    /// </summary>
    [Fact]
    public async Task GoogleSearchWithLinqFilteringAsync()
    {
#pragma warning disable CA1859 // Use concrete types when possible for improved performance - Sample intentionally demonstrates interface usage
        // Create an ITextSearch<GoogleWebPage> instance for type-safe LINQ filtering
        ITextSearch<GoogleWebPage> textSearch = new GoogleTextSearch(
            searchEngineId: TestConfiguration.Google.SearchEngineId,
            apiKey: TestConfiguration.Google.ApiKey);
#pragma warning restore CA1859

        var query = "What is the Semantic Kernel?";

        // Use LINQ filtering for type-safe search with compile-time validation
        var options = new TextSearchOptions<GoogleWebPage>
        {
            Top = 4,
            Filter = page => page.Title != null && page.Title.Contains("Semantic") && page.DisplayLink != null && page.DisplayLink.EndsWith(".com")
        };

        // Search and return strongly-typed results
        Console.WriteLine("\n--- Google Search with LINQ Filtering ---\n");
        KernelSearchResults<GoogleWebPage> searchResults = await textSearch.GetSearchResultsAsync(query, options);
        await foreach (GoogleWebPage page in searchResults.Results)
        {
            Console.WriteLine($"Title: {page.Title}");
            Console.WriteLine($"Snippet: {page.Snippet}");
            Console.WriteLine($"Link: {page.Link}");
            Console.WriteLine($"Display Link: {page.DisplayLink}");
            Console.WriteLine("---");
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> and use it to perform a search
    /// and return results as a collection of <see cref="BingWebPage"/> instances.
    /// </summary>
    [Fact]
    public async Task SearchForWebPagesAsync()
    {
        // Create an ITextSearch instance
        ITextSearch textSearch = this.UseBingSearch ?
            new BingTextSearch(
                apiKey: TestConfiguration.Bing.ApiKey) :
            new GoogleTextSearch(
                searchEngineId: TestConfiguration.Google.SearchEngineId,
                apiKey: TestConfiguration.Google.ApiKey);

        var query = "What is the Semantic Kernel?";

        // Search and return results using the implementation specific data model
        KernelSearchResults<object> objectResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 4 });
        if (this.UseBingSearch)
        {
            Console.WriteLine("\n--- Bing Web Page Results ---\n");
            await foreach (BingWebPage webPage in objectResults.Results)
            {
                Console.WriteLine($"Name:            {webPage.Name}");
                Console.WriteLine($"Snippet:         {webPage.Snippet}");
                Console.WriteLine($"Url:             {webPage.Url}");
                Console.WriteLine($"DisplayUrl:      {webPage.DisplayUrl}");
                Console.WriteLine($"DateLastCrawled: {webPage.DateLastCrawled}");
            }
        }
        else
        {
            Console.WriteLine("\n--- Google Web Page Results ---\n");
            await foreach (Google.Apis.CustomSearchAPI.v1.Data.Result result in objectResults.Results)
            {
                Console.WriteLine($"Title:       {result.Title}");
                Console.WriteLine($"Snippet:     {result.Snippet}");
                Console.WriteLine($"Link:        {result.Link}");
                Console.WriteLine($"DisplayLink: {result.DisplayLink}");
                Console.WriteLine($"Kind:        {result.Kind}");
            }
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> and use it to perform a search
    /// and return results as a collection of <see cref="TextSearchResult"/> instances.
    /// </summary>
    /// <remarks>
    /// Having a normalized format for search results is useful when you want to process the results
    /// for different search services in a consistent way.
    /// </remarks>
    [Fact]
    public async Task SearchForTextSearchResultsAsync()
    {
        // Create an ITextSearch instance
        ITextSearch textSearch = this.UseBingSearch ?
            new BingTextSearch(
                apiKey: TestConfiguration.Bing.ApiKey) :
            new GoogleTextSearch(
                searchEngineId: TestConfiguration.Google.SearchEngineId,
                apiKey: TestConfiguration.Google.ApiKey);

        var query = "What is the Semantic Kernel?";

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 4 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
        }
    }
}
