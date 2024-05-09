// Copyright (c) Microsoft. All rights reserved.
using Google.Apis.CustomSearchAPI.v1.Data;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Microsoft.SemanticKernel.Search;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="GoogleTextSearchService"/>.
/// </summary>
public sealed class GoogleSearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task SearchAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create a search service with Azure AI search
        var searchService = new GoogleTextSearchService(
            searchEngineId: TestConfiguration.Google.SearchEngineId,
            apiKey: TestConfiguration.Google.ApiKey);

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
        KernelSearchResults<Result> fullResults = await searchService.SearchAsync<Result>(query, new() { Count = 2, Offset = 6 });
        await foreach (Result result in fullResults.Results)
        {
            Console.WriteLine($"Title: {result.Title}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Snippet);
            Console.WriteLine(result.Link);
            Console.WriteLine(result.DisplayLink);
            Console.WriteLine(result.Kind);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }
}
