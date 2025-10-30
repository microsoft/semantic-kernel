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
        KernelSearchResults<string> searchResults = await textSearch.SearchAsync(query, new() { Top = 4 });
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
        KernelSearchResults<string> searchResults = await textSearch.SearchAsync(query, new() { Top = 4 });
        await foreach (string result in searchResults.Results)
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
            Console.WriteLine("\n——— Google Web Page Results ———\n");
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

    /// <summary>
    /// Show how to use the new generic <see cref="ITextSearch{TRecord}"/> interface with LINQ filtering for type-safe searches.
    /// This demonstrates the modernized text search functionality introduced in Issue #10456.
    /// </summary>
    /// <remarks>
    /// This example shows the intended pattern for the new generic interfaces.
    /// Currently demonstrates the concept using examples from the existing connectors in this sample suite:
    /// - BingTextSearch and GoogleTextSearch (this file)
    /// - VectorStoreTextSearch (Step4_Search_With_VectorStore.cs)
    /// </remarks>
    [Fact]
    public Task SearchWithLinqFilteringAsync()
    {
        // This example demonstrates the NEW generic interface pattern with LINQ filtering
        // that provides compile-time type safety and IntelliSense support

        Console.WriteLine("\n--- Type-Safe Search with Generic Interface and LINQ Filtering ---\n");
        Console.WriteLine("This demonstrates the modernized ITextSearch<TRecord> pattern from Issue #10456");
        Console.WriteLine("Key benefits:");
        Console.WriteLine("- Compile-time type safety (no runtime errors from property name typos)");
        Console.WriteLine("- IntelliSense support for filtering properties");
        Console.WriteLine("- LINQ expressions for complex filtering logic");
        Console.WriteLine("- Better developer experience with strongly-typed search results");
        Console.WriteLine();

        Console.WriteLine("=== Connectors Available in This Sample Suite ===");
        Console.WriteLine();

        Console.WriteLine("1. VectorStoreTextSearch<TRecord> (Step4_Search_With_VectorStore.cs)");
        Console.WriteLine("   [OK] Already implements ITextSearch<TRecord> with LINQ filtering:");
        Console.WriteLine("   var vectorSearch = new VectorStoreTextSearch<DataModel>(collection);");
        Console.WriteLine("   var options = new TextSearchOptions<DataModel>");
        Console.WriteLine("   {");
        Console.WriteLine("       Filter = record => record.Tag == \"Technology\" && record.Title.Contains(\"AI\")");
        Console.WriteLine("   };");
        Console.WriteLine("   var results = await vectorSearch.GetSearchResultsAsync(query, options);");
        Console.WriteLine();

        if (this.UseBingSearch)
        {
            Console.WriteLine("2. BingTextSearch (this file - BingSearchAsync())");
            Console.WriteLine("   [PLANNED] Pattern for future generic interface (once PR3 is merged):");
            Console.WriteLine("   var bingSearch = new BingTextSearch(apiKey);");
            Console.WriteLine("   var options = new TextSearchOptions<BingWebPage>");
            Console.WriteLine("   {");
            Console.WriteLine("       Top = 4,");
            Console.WriteLine("       Filter = page => page.Name.Contains(\"Microsoft\") && page.Snippet.Contains(\"AI\")");
            Console.WriteLine("   };");
            Console.WriteLine("   var results = await ((ITextSearch<BingWebPage>)bingSearch).GetSearchResultsAsync(query, options);");
            Console.WriteLine("   // Type-safe access: page.Name, page.Snippet, page.Url, page.DateLastCrawled");
        }
        else
        {
            Console.WriteLine("2. BingTextSearch (set UseBingSearch = true to see example)");
        }

        Console.WriteLine();
        Console.WriteLine("3. GoogleTextSearch (this file - GoogleSearchAsync())");
        Console.WriteLine("   [PLANNED] Pattern for future generic interface (once PR4 is merged):");
        Console.WriteLine("   // Note: GoogleWebPage is a conceptual type pending PR4 implementation");
        Console.WriteLine("   // The actual Google API currently uses: Google.Apis.CustomSearchAPI.v1.Data.Result");
        Console.WriteLine("   var googleSearch = new GoogleTextSearch(searchEngineId, apiKey);");
        Console.WriteLine("   var options = new TextSearchOptions<GoogleWebPage>");
        Console.WriteLine("   {");
        Console.WriteLine("       Top = 4,");
        Console.WriteLine("       Filter = page => page.Title.Contains(\"AI\") && page.DisplayLink.EndsWith(\".com\")");
        Console.WriteLine("   };");
        Console.WriteLine("   var results = await ((ITextSearch<GoogleWebPage>)googleSearch).GetSearchResultsAsync(query, options);");
        Console.WriteLine("   // Type-safe access: page.Title, page.Snippet, page.DisplayLink, page.Link");
        Console.WriteLine();

        Console.WriteLine("=== Key Technical Benefits ===");
        Console.WriteLine();
        Console.WriteLine("[OK] Compile-time validation - no more runtime property name errors");
        Console.WriteLine("[OK] IntelliSense support - IDE shows available properties for each connector");
        Console.WriteLine("[OK] Type safety - strongly typed search results and filtering");
        Console.WriteLine("[OK] LINQ expressions - familiar &&, ||, Contains(), StartsWith(), comparisons, etc.");
        Console.WriteLine("[OK] C# version compatibility - expressions work across C# 12, 13, and 14+");
        Console.WriteLine("[OK] 100% backward compatibility - existing ITextSearch code unchanged");
        Console.WriteLine();

        Console.WriteLine("=== Example LINQ Filtering Patterns ===");
        Console.WriteLine();
        Console.WriteLine("// Bing: Filter web pages by content and metadata");
        Console.WriteLine("Filter = page => page.Name.Contains(\"Microsoft\") && page.DateLastCrawled > DateTime.Now.AddDays(-7)");
        Console.WriteLine("//       ↑ String.Contains (instance method) - works in all C# versions");
        Console.WriteLine();
        Console.WriteLine("// Google: Filter search results by domain and content");
        Console.WriteLine("Filter = result => result.Title.Contains(\"AI\") && result.DisplayLink.EndsWith(\".edu\")");
        Console.WriteLine("//                 ↑ String.Contains (instance method) - works in all C# versions");
        Console.WriteLine();
        Console.WriteLine("// Vector Store: Filter custom record types with complex logic");
        Console.WriteLine("Filter = record => record.Category == \"Technology\" && record.Score > 0.75 && record.Tags.Any(t => t == \"AI\")");
        Console.WriteLine("//                                                                                         ↑ Use Any() for collections");
        Console.WriteLine();
        Console.WriteLine("// C# 14 Compatibility Note:");
        Console.WriteLine("// - String.Contains() (instance method): ✅ Works in all C# versions");
        Console.WriteLine("// - For collection filtering, use Any() or Where(): array.Any(x => x == value)");
        Console.WriteLine("// - Avoid collection.Contains(item) in expressions (C# 14 resolution changes)");
        Console.WriteLine();

        Console.WriteLine("The VectorStoreTextSearch already demonstrates this pattern in Step4!");
        Console.WriteLine("See Step4_Search_With_VectorStore.cs for working generic interface examples.");
        Console.WriteLine();
        Console.WriteLine("This modernization is part of the structured PR series for Issue #10456:");
        Console.WriteLine("PR1: Core generic interfaces [OK]");
        Console.WriteLine("PR2: VectorStoreTextSearch implementation [OK]");
        Console.WriteLine("PR3: BingTextSearch connector (future) [PLANNED]");
        Console.WriteLine("PR4: GoogleTextSearch connector (future) [PLANNED]");
        Console.WriteLine("PR5: TavilyTextSearch & BraveTextSearch connectors (future) [PLANNED]");
        Console.WriteLine("PR6: Samples and documentation (this PR) [OK]");

        return Task.CompletedTask;
    }
}
