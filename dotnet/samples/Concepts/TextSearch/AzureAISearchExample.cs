// Copyright (c) Microsoft. All rights reserved.

using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="AzureAITextSearchService"/>.
/// </summary>
public sealed class AzureAISearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="AzureAITextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseAzureAITextSearchAsync()
    {
        var query = "What is the Semantic Kernel?";
        var IndexName = TestConfiguration.AzureAISearch.IndexName;

        // Create a search service with Azure AI search
        var searchService = new AzureAITextSearchService(
            endpoint: TestConfiguration.AzureAISearch.Endpoint,
            adminKey: TestConfiguration.AzureAISearch.ApiKey);

        // Search with TextSearchResult result type
        AzureAISearchExecutionSettings settings = new() { Index = IndexName, Count = 2, Offset = 2, NameField = "title", ValueField = "chunk", LinkField = "metadata_spo_item_weburi" };
        KernelSearchResults<TextSearchResult> textResults = await ((ITextSearchService<TextSearchResult>)searchService).SearchAsync(query, settings);
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name: {result.Name}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.Value);
            Console.WriteLine(result.Link);
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }

        // Search with a the default result type
        KernelSearchResults<SearchDocument> fullResults = await ((ITextSearchService<SearchDocument>)searchService).SearchAsync(query, new() { Index = IndexName, Count = 2, Offset = 6 });
        await foreach (SearchDocument result in fullResults.Results)
        {
            Console.WriteLine($"Title: {result.GetString("title")}");
            Console.WriteLine($"Chunk Id: {result.GetString("chunk_id")}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
            Console.WriteLine(result.GetString("chunk"));
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }
}
