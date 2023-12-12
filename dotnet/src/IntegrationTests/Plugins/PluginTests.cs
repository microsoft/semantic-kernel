// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;

public class PluginTests
{
    [Theory]
    [InlineData("https://www.klarna.com/.well-known/ai-plugin.json", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    public async Task QueryKlarnaOpenAIPluginAsync(
    string pluginEndpoint,
    string name,
    string functionName,
    string query,
    int size,
    int budget,
    string countryCode)
    {
        // Arrange
        var kernel = new Kernel();
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFromOpenAIAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenAIFunctionExecutionParameters(httpClient));

        var arguments = new KernelArguments();
        arguments["q"] = query;
        arguments["size"] = size.ToString(System.Globalization.CultureInfo.InvariantCulture);
        arguments["budget"] = budget.ToString(System.Globalization.CultureInfo.InvariantCulture);
        arguments["countryCode"] = countryCode;

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }

    [Theory]
    [InlineData("https://www.klarna.com/us/shopping/public/openai/v0/api-docs/", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    public async Task QueryKlarnaOpenApiPluginAsync(
        string pluginEndpoint,
        string name,
        string functionName,
        string query,
        int size,
        int budget,
        string countryCode)
    {
        // Arrange
        var kernel = new Kernel();
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiFunctionExecutionParameters(httpClient));

        var arguments = new KernelArguments();
        arguments["q"] = query;
        arguments["size"] = size.ToString(System.Globalization.CultureInfo.InvariantCulture);
        arguments["budget"] = budget.ToString(System.Globalization.CultureInfo.InvariantCulture);
        arguments["countryCode"] = countryCode;

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }

    [Theory]
    [InlineData("https://www.klarna.com/us/shopping/public/openai/v0/api-docs/", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    public async Task QueryKlarnaOpenApiPluginRunAsync(
        string pluginEndpoint,
        string name,
        string functionName,
        string query,
        int size,
        int budget,
        string countryCode)
    {
        // Arrange
        var kernel = new Kernel();
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiFunctionExecutionParameters(httpClient));

        var arguments = new KernelArguments();
        arguments["q"] = query;
        arguments["size"] = size.ToString(System.Globalization.CultureInfo.InvariantCulture);
        arguments["budget"] = budget.ToString(System.Globalization.CultureInfo.InvariantCulture);
        arguments["countryCode"] = countryCode;

        // Act
        var result = (await kernel.InvokeAsync(plugin[functionName], arguments)).GetValue<RestApiOperationResponse>();

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.ExpectedSchema);
        Assert.NotNull(result.Content);
        Assert.True(result.IsValid());
    }

    [Theory]
    [InlineData("https://raw.githubusercontent.com/sisbell/chatgpt-plugin-store/main/manifests/instacart.com.json",
        "Instacart",
        "create",
        "{\"title\":\"Shopping List\", \"ingredients\": [\"Flour\"], \"question\": \"what ingredients do I need to make chocolate cookies?\", \"partnerName\": \"OpenAI\" }"
        )]
    public async Task QueryInstacartPluginAsync(
        string pluginEndpoint,
        string name,
        string functionName,
        string payload)
    {
        // Arrange
        var kernel = new Kernel();
        using HttpClient httpClient = new();

        //note that this plugin is not compliant according to the underlying validator in SK
        var plugin = await kernel.ImportPluginFromOpenAIAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

        var arguments = new KernelArguments();
        arguments["payload"] = payload;

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }

    [Theory]
    [InlineData("Plugins/instacart-ai-plugin.json",
        "Instacart",
        "create",
        "{\"title\":\"Shopping List\", \"ingredients\": [\"Flour\"], \"question\": \"what ingredients do I need to make chocolate cookies?\", \"partnerName\": \"OpenAI\" }"
        )]
    public async Task QueryInstacartPluginFromStreamAsync(
        string pluginFilePath,
        string name,
        string functionName,
        string payload)
    {
        // Arrange
        using (var stream = System.IO.File.OpenRead(pluginFilePath))
        {
            var kernel = new Kernel();
            using HttpClient httpClient = new();

            //note that this plugin is not compliant according to the underlying validator in SK
            var plugin = await kernel.ImportPluginFromOpenAIAsync(
                name,
                stream,
                new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

            var arguments = new KernelArguments();
            arguments["payload"] = payload;

            // Act
            await plugin[functionName].InvokeAsync(kernel, arguments);
        }
    }

    [Theory]
    [InlineData("Plugins/instacart-ai-plugin.json",
        "Instacart",
        "create",
        "{\"title\":\"Shopping List\", \"ingredients\": [\"Flour\"], \"question\": \"what ingredients do I need to make chocolate cookies?\", \"partnerName\": \"OpenAI\" }"
        )]
    public async Task QueryInstacartPluginUsingRelativeFilePathAsync(
        string pluginFilePath,
        string name,
        string functionName,
        string payload)
    {
        // Arrange
        var kernel = new Kernel();
        using HttpClient httpClient = new();

        //note that this plugin is not compliant according to the underlying validator in SK
        var plugin = await kernel.ImportPluginFromOpenAIAsync(
            name,
            pluginFilePath,
            new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

        var arguments = new KernelArguments();
        arguments["payload"] = payload;

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }
}
