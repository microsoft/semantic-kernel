// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to create and use a <see cref="TextSearchPlugin{T}"/>.
/// </summary>
public sealed class TextSearchPluginExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="TextSearchPlugin{T}"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UseTextSearchPluginWithBingTextSearchAsync()
    {
        // Create a search service with Bing search service
        var searchService = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a kernel with Bing search service and add a text search plugin
        Kernel kernel = new();
        var textSearchResultPlugin = new TextSearchPlugin<TextSearchResult>(searchService);
        kernel.ImportPluginFromObject(textSearchResultPlugin, "TextSearch");
        var bingWebPagePlugin = new TextSearchPlugin<BingWebPage>(searchService);
        kernel.ImportPluginFromObject(bingWebPagePlugin, "BingSearch");

        // Invoke the plugin to perform a text search and return string values
        var question = "What is the Semantic Kernel?";
        var function = kernel.Plugins["TextSearch"]["Search"];
        var result = await kernel.InvokeAsync(function, new() { ["query"] = question });

        Console.WriteLine(result);

        // Invoke the plugin to perform a text search and return BingWebPage values
        function = kernel.Plugins["BingSearch"]["Search"];
        result = await kernel.InvokeAsync(function, new() { ["query"] = question, ["count"] = 2 });

        Console.WriteLine(result);
    }
}
