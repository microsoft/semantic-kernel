// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Google.Apis.CustomSearchAPI.v1.Data;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="GoogleTextSearch"/>.
/// </summary>
public sealed class GoogleSearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingGoogleTextSearchAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create an ITextSearch instance using Google search
        var textSearch = new GoogleTextSearch(
            searchEngineId: TestConfiguration.Google.SearchEngineId,
            apiKey: TestConfiguration.Google.ApiKey);

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
        KernelSearchResults<Result> fullResults = await ((ITextSearch<Result>)textSearch).SearchAsync(query, new() { Count = 2, Offset = 6 });
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

    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseGoogleTextSearchWithCustomMapperAsync()
    {
        var query = "What is the Semantic Kernel?";

        // Create an ITextSearch instance using Google search
        ITextSearch<string> textSearch = new GoogleTextSearch(
            searchEngineId: TestConfiguration.Google.SearchEngineId,
            apiKey: TestConfiguration.Google.ApiKey,
            options: new()
            {
                MapToString = result => JsonSerializer.Serialize(result),
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
