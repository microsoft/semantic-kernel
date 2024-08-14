// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="BingTextSearch"/>.
/// </summary>
public sealed class BingSearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingBingTextSearchAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create an ITextSearch instance using Bing search
        var bingTextSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);

        // Search with String textResult type
        KernelSearchResults<string> stringResults = await ((ITextSearch<string>)bingTextSearch).SearchAsync(query, new() { Count = 4, Offset = 0 });
        Console.WriteLine("--- String Results ---\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult textResult type
        KernelSearchResults<TextSearchResult> textResults = await ((ITextSearch<TextSearchResult>)bingTextSearch).SearchAsync(query, new() { Count = 4, Offset = 4 });
        Console.WriteLine("\n--- Text Search Results ---\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default textResult type
        KernelSearchResults<BingWebPage> fullResults = await ((ITextSearch<BingWebPage>)bingTextSearch).SearchAsync(query, new() { Count = 4, Offset = 8 });
        Console.WriteLine("\n--- Bing Web Page Results ---\n");
        await foreach (BingWebPage result in fullResults.Results)
        {
            Console.WriteLine($"Name:            {result.Name}");
            Console.WriteLine($"Snippet:         {result.Snippet}");
            Console.WriteLine($"Url:             {result.Url}");
            Console.WriteLine($"DisplayUrl:      {result.DisplayUrl}");
            Console.WriteLine($"DateLastCrawled: {result.DateLastCrawled}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseBingTextSearchWithCustomMapperAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create an ITextSearch instance using Bing search
        ITextSearch<string> textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey, options: new()
        {
            MapToString = webPage => JsonSerializer.Serialize(webPage),
        });

        // Search with TextSearchResult textResult type
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Count = 2, Offset = 4 });
        Console.WriteLine("--- Serialized JSON Results ---");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    /// <summary>
    /// Show how to create a <see cref="BingTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseBingTextSearchWithSiteFilterAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create an ITextSearch instance using Bing search
        ITextSearch<string> textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey, options: new()
        {
            MapToString = webPage => JsonSerializer.Serialize(webPage),
        });

        // Search with TextSearchResult textResult type
        SearchOptions searchOptions = new() { Count = 4, Offset = 0 };
        searchOptions.BasicFilter = new BasicFilterOptions().Equality("site", "devblogs.microsoft.com");
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, searchOptions);
        Console.WriteLine("--- Microsoft Developer Blogs Results ---");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    /// <summary>
    /// Show how to create a <see cref="KernelFunction"/> from an instance of <see cref="BingTextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingBingTextSearchAsPluginAsync()
    {
        Kernel kernel = new();
        var query = "What is the Semantic Kernel?";

        // Create an ITextSearch instance using Bing search
        var bingTextSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);

        // Search with String result type
        var textSearchPlugin = TextSearchKernelPluginFactory.CreateFromTextSearch(bingTextSearch, "TextSearchPlugin");
        var textResults = await kernel.InvokeAsync<IEnumerable<string>>(textSearchPlugin["Search"], new() { ["query"] = query });
        Console.WriteLine("--- String Results ---\n");
        foreach (string textResult in textResults!)
        {
            Console.WriteLine(textResult);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult result type
        var textSearchResultPlugin = TextSearchKernelPluginFactory.CreateFromTextSearchResults(bingTextSearch, "TextSearchResultPlugin");
        var textSearchResults = await kernel.InvokeAsync<IEnumerable<TextSearchResult>>(textSearchResultPlugin["GetSearchResults"], new() { ["query"] = query });
        Console.WriteLine("\n--- Text Search Results ---\n");
        foreach (TextSearchResult textSearchResult in textSearchResults!)
        {
            Console.WriteLine($"Name:  {textSearchResult.Name}");
            Console.WriteLine($"Value: {textSearchResult.Value}");
            Console.WriteLine($"Link:  {textSearchResult.Link}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with BingWebPage result type
        var bingWebPagePlugin = BingTextSearchKernelPluginFactory.CreateFromBingWebPages(bingTextSearch, "BingWebPagePlugin");
        var bingWebPages = await kernel.InvokeAsync<IEnumerable<BingWebPage>>(bingWebPagePlugin["GetBingWebPages"], new() { ["query"] = query });
        Console.WriteLine("\n--- Bing Web Page Results ---\n");
        foreach (BingWebPage bingWebPage in bingWebPages!)
        {
            Console.WriteLine($"Name:            {bingWebPage.Name}");
            Console.WriteLine($"Snippet:         {bingWebPage.Snippet}");
            Console.WriteLine($"Url:             {bingWebPage.Url}");
            Console.WriteLine($"DisplayUrl:      {bingWebPage.DisplayUrl}");
            Console.WriteLine($"DateLastCrawled: {bingWebPage.DateLastCrawled}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }
}
