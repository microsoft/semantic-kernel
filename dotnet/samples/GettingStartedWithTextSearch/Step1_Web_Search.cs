// Copyright (c) Microsoft. All rights reserved.

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
        IAsyncEnumerable<string> searchResults = textSearch.SearchAsync(query, 4);
        await foreach (string result in searchResults)
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
        IAsyncEnumerable<string> searchResults = textSearch.SearchAsync(query, 4);
        await foreach (string result in searchResults)
        {
            Console.WriteLine(result);
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
        IAsyncEnumerable<object> objectResults = textSearch.GetSearchResultsAsync(query, 4);
        if (this.UseBingSearch)
        {
            Console.WriteLine("\n--- Bing Web Page Results ---\n");
            await foreach (BingWebPage webPage in objectResults)
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
            Console.WriteLine("\n——— Google Web Page Results ———\n");
            await foreach (Google.Apis.CustomSearchAPI.v1.Data.Result result in objectResults)
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
        IAsyncEnumerable<TextSearchResult> textResults = textSearch.GetTextSearchResultsAsync(query, 4);
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
        }
    }
}
