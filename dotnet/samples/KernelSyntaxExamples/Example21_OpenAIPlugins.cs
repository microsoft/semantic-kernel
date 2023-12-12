// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

// ReSharper disable once InconsistentNaming
public static class Example21_OpenAIPlugins
{
    public static async Task RunAsync()
    {
        // Uncomment after filling the template below
        // await RunOpenAIPluginAsync();

        // --------------- Example using Klarna's OpenAI plugin ------------------------
        await CallKlarnaAsync();
    }

    /// <summary>
    /// Generic template on how to call OpenAI plugins
    /// </summary>
    public static async Task RunOpenAIPluginAsync()
    {
        Kernel kernel = new();

        // This HTTP client is optional. SK will fallback to a default internal one if omitted.
        using HttpClient httpClient = new();

        // Import an Open AI plugin via URI
        var plugin = await kernel.ImportPluginFromOpenAIAsync("<plugin name>", new Uri("<OpenAI-plugin>"), new OpenAIFunctionExecutionParameters(httpClient));

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments { ["<parameter-name>"] = "<parameter-value>" };

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["<function-name>"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("Function execution result: {0}", result?.Content?.ToString());
    }

    public static async Task CallKlarnaAsync()
    {
        Kernel kernel = new();

        var plugin = await kernel.ImportPluginFromOpenAIAsync("Klarna", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"));

        var arguments = new KernelArguments();
        arguments["q"] = "Laptop";      // Category or product that needs to be searched for.
        arguments["size"] = "3";        // Number of products to return
        arguments["budget"] = "200";    // Maximum price of the matching product in local currency
        arguments["countryCode"] = "US";// ISO 3166 country code with 2 characters based on the user location.
                                        // Currently, only US, GB, DE, SE and DK are supported.

        var functionResult = await kernel.InvokeAsync(plugin["productsUsingGET"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("Function execution result: {0}", result?.Content?.ToString());
    }
}
