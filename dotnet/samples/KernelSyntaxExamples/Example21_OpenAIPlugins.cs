// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example21_OpenAIPlugins(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Generic template on how to call OpenAI plugins
    /// </summary>
    [Fact]
    public async Task RunOpenAIPluginAsync()
    {
        Kernel kernel = new();

        // This HTTP client is optional. SK will fallback to a default internal one if omitted.
        using HttpClient httpClient = new();

        // Import an Open AI plugin via URI
        var plugin = await kernel.ImportPluginFromOpenApiAsync("Test", new Uri("https://localhost:7031/swagger/v1/swagger.json"), new OpenAIFunctionExecutionParameters(httpClient));

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments { ["name"] = "fake-name" };

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["Test-get"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        WriteLine($"Function execution result: {result?.Content}");
    }

    [Fact]
    public async Task CallKlarnaAsync()
    {
        Kernel kernel = new();

        var plugin = await kernel.ImportPluginFromOpenAIAsync("Klarna", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"));

        var arguments = new KernelArguments
        {
            ["q"] = "Laptop",      // Category or product that needs to be searched for.
            ["size"] = "3",        // Number of products to return
            ["budget"] = "200",    // Maximum price of the matching product in local currency
            ["countryCode"] = "US" // ISO 3166 country code with 2 characters based on the user location.
        };
        // Currently, only US, GB, DE, SE and DK are supported.

        var functionResult = await kernel.InvokeAsync(plugin["productsUsingGET"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        WriteLine($"Function execution result: {result?.Content}");
    }
}
