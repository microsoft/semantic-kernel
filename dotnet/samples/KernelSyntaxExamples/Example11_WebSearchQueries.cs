// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example11_WebSearchQueries : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        WriteLine("======== WebSearchQueries ========");

        Kernel kernel = new();

        // Load native plugins
        var bing = kernel.ImportPluginFromType<SearchUrlPlugin>("search");

        // Run
        var ask = "What's the tallest building in Europe?";
        var result = await kernel.InvokeAsync(bing["BingSearchUrl"], new() { ["query"] = ask });

        WriteLine(ask + "\n");
        WriteLine(result.GetValue<string>());

        /* Expected output: 
        * ======== WebSearchQueries ========
        * What's the tallest building in Europe?
        * 
        * https://www.bing.com/search?q=What%27s%20the%20tallest%20building%20in%20Europe%3F
        * == DONE ==
        */
    }

    public Example11_WebSearchQueries(ITestOutputHelper output) : base(output)
    {
    }
}
