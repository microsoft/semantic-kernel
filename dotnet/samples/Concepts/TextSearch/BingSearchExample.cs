// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using System.Text.RegularExpressions;
using HtmlAgilityPack;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="BingTextSearch"/>.
/// </summary>
public sealed partial class BingSearchExample(ITestOutputHelper output) : BaseTest(output)
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
        SearchOptions searchOptions = new() { Count = 4, Offset = 0, BasicFilter = new BasicFilterOptions().Equality("site", "devblogs.microsoft.com") };
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

        // Search with BingWebPage result type
        var fullWebPagePlugin = BingTextSearchKernelPluginFactory.CreateFromBingWebPages(bingTextSearch, "FullWebPagePlugin", null, CreateGetFullWebPagesOptions(bingTextSearch));
        var fullWebPages = await kernel.InvokeAsync<IEnumerable<TextSearchResult>>(fullWebPagePlugin["GetFullWebPages"], new() { ["query"] = query });
        Console.WriteLine("\n--- Full Web Page Results ---\n");
        foreach (TextSearchResult fullWebPage in fullWebPages!)
        {
            Console.WriteLine($"Name:  {fullWebPage.Name}");
            Console.WriteLine($"Value: {fullWebPage.Value}");
            Console.WriteLine($"Link:  {fullWebPage.Link}");
            Console.WriteLine("------------------------------------------------------------------------------------------------------------------");
        }
    }

    public static KernelPluginFromTextSearchOptions CreateGetFullWebPagesOptions(ITextSearch<BingWebPage> textSearch)
    {
        return new()
        {
            Functions =
            [
                GetFullWebPages(textSearch),
            ]
        };
    }

    private static KernelFunctionFromTextSearchOptions GetFullWebPages(ITextSearch<BingWebPage> textSearch, BasicFilterOptions? basicFilter = null)
    {
        async Task<IEnumerable<TextSearchResult>> GetFullWebPagesAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                arguments.TryGetValue("query", out var query);
                if (string.IsNullOrEmpty(query?.ToString()))
                {
                    return [];
                }

                var parameters = function.Metadata.Parameters;

                arguments.TryGetValue("count", out var count);
                arguments.TryGetValue("skip", out var skip);
                SearchOptions searchOptions = new()
                {
                    Count = (count as int?) ?? GetDefaultValue(parameters, "count", 2),
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0),
                    BasicFilter = basicFilter
                };

                var result = await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                var resultList = new List<TextSearchResult>();

                using HttpClient client = new();
                await foreach (var item in result.Results.WithCancellation(cancellationToken).ConfigureAwait(false))
                {
                    string? value = item.Snippet;
                    try
                    {
                        if (item.Url is not null)
                        {
                            value = await client.GetStringAsync(new Uri(item.Url), cancellationToken);
                            value = ConvertHtmlToPlainText(value);
                        }
                    }
                    catch (HttpRequestException)
                    {
                    }

                    resultList.Add(new() { Name = item.Name, Value = value, Link = item.Url });
                }

                return resultList;
            }
            catch (Exception)
            {
                throw;
            }
        }

        return new()
        {
            Delegate = GetFullWebPagesAsync,
            FunctionName = "GetFullWebPages",
            Description = "Perform a search for content related to the specified query. The search will return the name, full web page content and link for the related content.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };
    }

    private static int GetDefaultValue(IReadOnlyList<KernelParameterMetadata> parameters, string name, int defaultValue)
    {
        var value = parameters.FirstOrDefault(parameter => parameter.Name == name)?.DefaultValue;
        return value is int intValue ? intValue : defaultValue;
    }
    private static string ConvertHtmlToPlainText(string html)
    {
        HtmlDocument doc = new();
        doc.LoadHtml(html);

        string text = doc.DocumentNode.InnerText;
        text = MyRegex().Replace(text, " "); // Remove unnecessary whitespace  
        return text.Trim();
    }

    [GeneratedRegex(@"\s+")]
    private static partial Regex MyRegex();
}
