// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="TextSearchKernelPluginFactory"/>.
/// </summary>
public sealed class CreateFromTextSearchExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseCreateFromTextSearchWithBingTextSearchAsync()
    {
        // Create a search service with Bing search service
        var searchService = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a kernel with Bing search service and add a text search plugin
        Kernel kernel = new();
        var textSearchPlugin = TextSearchKernelPluginFactory.CreateFromTextSearch(searchService, "TextSearchPlugin");
        kernel.Plugins.Add(textSearchPlugin);
        var textSearchResultsPlugin = TextSearchKernelPluginFactory.CreateFromTextSearchResults(searchService, "TextSearchResultsPlugin");
        kernel.Plugins.Add(textSearchResultsPlugin);

        // Invoke the plugin to perform a text search and return string values
        var question = "What is the Semantic Kernel?";
        var function = kernel.Plugins["TextSearchPlugin"]["Search"];
        var result = await kernel.InvokeAsync(function, new() { ["query"] = question });
        Console.WriteLine(result);
        var stringList = result.GetValue<IReadOnlyList<string>>();
        Console.WriteLine(string.Join('\n', stringList!));

        // Invoke the plugin to perform a text search and return BingWebPage values
        function = kernel.Plugins["TextSearchResultsPlugin"]["Search"];
        result = await kernel.InvokeAsync(function, new() { ["query"] = question, ["count"] = 2 });
        var pageList = result.GetValue<IReadOnlyList<BingWebPage>>();
        Console.WriteLine(JsonSerializer.Serialize(pageList));
    }

    /// <summary>
    /// Show how to create a custom <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseCustomizedCreateFromTextSearchWithBingTextSearchAsync()
    {
        // Create a search service with Bing search service
        var searchService = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a kernel with Bing search service and add a text search plugin
        Kernel kernel = new();
        var textSearchResultPlugin = TextSearchKernelPluginFactory.CreateFromTextSearch(
            searchService, "CustomSearch", "Custom Search Plugin", CreateCustomOptions(searchService));
        kernel.Plugins.Add(textSearchResultPlugin);

        // Invoke the plugin to perform a text search and return string values
        var question = "What is the Semantic Kernel?";
        var function = kernel.Plugins["CustomSearch"]["SearchForTenResults"];
        var result = await kernel.InvokeAsync(function, new() { ["query"] = question });
        var resultList = result.GetValue<IReadOnlyList<TextSearchResult>>();
        Console.WriteLine(JsonSerializer.Serialize(resultList));
    }

#pragma warning disable CA1859 // Use concrete types when possible for improved performance
    private static KernelPluginFromTextSearchOptions CreateCustomOptions(ITextSearch<TextSearchResult> textSearch)
#pragma warning restore CA1859 // Use concrete types when possible for improved performance
    {
        List<KernelFunctionFromTextSearchOptions> functions = [];
        KernelPluginFromTextSearchOptions options = new()
        {
            Functions = functions
        };

        async Task<string> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                arguments.TryGetValue("query", out var query);
                query = query?.ToString() ?? string.Empty;

                var parameters = function.Metadata.Parameters;

                arguments.TryGetValue("count", out var count);
                arguments.TryGetValue("count", out var skip);
                SearchOptions searchOptions = new()
                {
                    Count = (count as int?) ?? 2,
                    Offset = (skip as int?) ?? 0,
                };

                var result = await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                var resultList = await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
                return options.MapToString!(resultList);
            }
            catch (Exception)
            {
                throw;
            }
        }

        KernelFunctionFromTextSearchOptions search = new()
        {
            Delegate = SearchAsync,
            FunctionName = "SearchForTenResults",
            Description = "Perform a search for content related to the specified query and return 10 results",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = true, DefaultValue = 10 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(string) },
        };
        functions.Add(search);

        return options;
    }
}
