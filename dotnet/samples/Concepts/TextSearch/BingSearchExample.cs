// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
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
        var textSearch = new BingTextSearch(apiKey: TestConfiguration.Bing.ApiKey);

        // Search with String result type
        KernelSearchResults<string> stringResults = await ((ITextSearch<string>)textSearch).SearchAsync(query, new() { Count = 2, Offset = 4 });
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult result type
        KernelSearchResults<TextSearchResult> textResults = await ((ITextSearch<TextSearchResult>)textSearch).SearchAsync(query, new() { Count = 2, Offset = 4 });
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Value);
            Console.WriteLine(result.Link);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<BingWebPage> fullResults = await ((ITextSearch<BingWebPage>)textSearch).SearchAsync(query, new() { Count = 2, Offset = 6 });
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

        // Search with TextSearchResult result type
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Count = 2, Offset = 4 });
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }
}
