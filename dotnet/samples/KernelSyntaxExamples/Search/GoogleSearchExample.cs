// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Examples;
using Google.Apis.CustomSearchAPI.v1.Data;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Microsoft.SemanticKernel.Search;
using Xunit;
using Xunit.Abstractions;

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
    public async Task RunAsync()
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
            WriteLine(result);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult result type
        KernelSearchResults<TextSearchResult> textResults = await searchService.SearchAsync<TextSearchResult>(query, new() { Count = 2, Offset = 4 });
        await foreach (TextSearchResult result in textResults.Results)
        {
            WriteLine($"Name: {result.Name}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Value);
            WriteLine(result.Link);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<Result> fullResults = await searchService.SearchAsync<Result>(query, new() { Count = 2, Offset = 6 });
        await foreach (Result result in fullResults.Results)
        {
            WriteLine($"Title: {result.Title}");
            WriteLine("------------------------------------------------------------------------------------------------------------------");
            WriteLine(result.Snippet);
            WriteLine(result.Link);
            WriteLine(result.DisplayLink);
            WriteLine(result.Kind);
            WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }
}
