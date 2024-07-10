// Copyright (c) Microsoft. All rights reserved.

using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="AzureAITextSearch"/>.
/// </summary>
public sealed class AzureAISearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="AzureAITextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseAzureAITextSearchAsync()
    {
        var query = "What is the Semantic Kernel?";
        var indexName = TestConfiguration.AzureAISearch.IndexName;

        // Create an ITextSearch instance using Azure AI search
        var searchService = new AzureAITextSearch(
            endpoint: TestConfiguration.AzureAISearch.Endpoint,
            adminKey: TestConfiguration.AzureAISearch.ApiKey,
            indexName: indexName);

        // Search with String result type
        KernelSearchResults<string> stringResults = await ((ITextSearch<string>)searchService).SearchAsync(query);
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with TextSearchResult result type
        KernelSearchResults<TextSearchResult> textResults = await ((ITextSearch<TextSearchResult>)searchService).SearchAsync(query);
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Value);
            Console.WriteLine(result.Link);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<SearchDocument> fullResults = await ((ITextSearch<SearchDocument>)searchService).SearchAsync(query, new() { Count = 2, Offset = 6 });
        await foreach (SearchDocument result in fullResults.Results)
        {
            Console.WriteLine($"Title: {result.GetString("title")}");
            Console.WriteLine($"Chunk Id: {result.GetString("chunk_id")}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.GetString("chunk"));
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    /// <summary>
    /// Show how to create a <see cref="AzureAITextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseGoogleTextSearchWithCustomMapperAsync()
    {
        var query = "What is the Semantic Kernel?";
        var indexName = TestConfiguration.AzureAISearch.IndexName;

        // Create an ITextSearch instance using Azure AI search
        ITextSearch<TextSearchResult> textSearch = new AzureAITextSearch(
            endpoint: TestConfiguration.AzureAISearch.Endpoint,
            adminKey: TestConfiguration.AzureAISearch.ApiKey,
            indexName: indexName,
            options: new()
            {
                MapToTextSearchResult = document => new TextSearchResult(
                    name: document["title"]?.ToString() ?? string.Empty,
                    value: document["chunk"]?.ToString() ?? string.Empty,
                    link: document["metadata_spo_item_weburi"]?.ToString() ?? string.Empty,
                    innerResult: document),
            });

        // Search with TextSearchResult result type
        KernelSearchResults<TextSearchResult> textResults = await textSearch.SearchAsync(query, new() { Count = 2, Offset = 4 });
        await foreach (var result in textResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Value);
            Console.WriteLine(result.Link);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }
}
