// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;

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
    public async Task SearchForWebPagesAsync()
    {
        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);

        var query = "What is the Semantic Kernel?";

        // Search and return s results as BingWebPage items
        KernelSearchResults<object> webPages = await textSearch.GetSearchResultsAsync(query, new() { Top = 4, Skip = 8 });
        Console.WriteLine("\n--- Bing Web Page Results ---\n");
        await foreach (BingWebPage webPage in webPages.Results)
        {
            Console.WriteLine($"Name:            {webPage.Name}");
            Console.WriteLine($"Snippet:         {webPage.Snippet}");
            Console.WriteLine($"Url:             {webPage.Url}");
            Console.WriteLine($"DisplayUrl:      {webPage.DisplayUrl}");
            Console.WriteLine($"DateLastCrawled: {webPage.DateLastCrawled}");
            WriteHorizontalRule();
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> and use it to perform a search
    /// and return results as a collection of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <remarks>
    /// Having a normalized format for search results is useful when you want to process the results
    /// for different search services in a consistent way.
    /// </remarks>
    [Fact]
    public async Task SearchForTextSearchResultsAsync()
    {
        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);

        var query = "What is the Semantic Kernel?";

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
    }
}
