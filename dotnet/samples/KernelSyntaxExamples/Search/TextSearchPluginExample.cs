// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Xunit;
using Xunit.Abstractions;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="TextSearchPlugin"/>.
/// </summary>
public sealed class TextSearchPluginExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="TextSearchPlugin"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        // Create a search service with Bing search service
        var searchService = new BingTextSearchService(
            endpoint: TestConfiguration.Bing.Endpoint,
            apiKey: TestConfiguration.Bing.ApiKey);

        // Build a kernel with Bing search service and add a text search plugin
        Kernel kernel = new();
        var searchPlugin = new TextSearchPlugin(searchService);
        kernel.ImportPluginFromObject(searchPlugin, "TextSearch");

        // Invoke the plugin to perform a text search
        var question = "What is the Semantic Kernel?";
        var function = kernel.Plugins["TextSearch"]["Search"];
        var result = await kernel.InvokeAsync(function, new() { ["query"] = question });

        WriteLine(result);
    }
}
