// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.OpenApi;

public class PluginTests
{
    [Theory(Skip = "Add a valid plugin endpoint.")]
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

        var arguments = new KernelArguments
        {
            ["q"] = query,
            ["size"] = size,
            ["max_price"] = budget.ToString(System.Globalization.CultureInfo.InvariantCulture),
            ["countryCode"] = countryCode
        };

        // Act
        var result = (await kernel.InvokeAsync(plugin[functionName], arguments)).GetValue<RestApiOperationResponse>();

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.ExpectedSchema);
        Assert.NotNull(result.Content);
        Assert.True(result.IsValid());
    }

    [Theory]
    [InlineData("Plugins/OpenApi/instacart-service.yaml",
        "Instacart",
        "create",
        """{"title":"Shopping List", "ingredients": ["Flour"], "question": "what ingredients do I need to make chocolate cookies?", "partner_name": "OpenAI" }"""
        )]
    public async Task QueryInstacartPluginFromStreamAsync(
        string pluginFilePath,
        string name,
        string functionName,
        string payload)
    {
        // Arrange
        using var stream = System.IO.File.OpenRead(pluginFilePath);
        using HttpClient httpClient = new();
        var kernel = new Kernel();

        // note that this plugin is not compliant according to the underlying validator in SK
        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            name,
            stream,
            new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });

        var arguments = new KernelArguments
        {
            ["payload"] = payload
        };

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }

    [Theory]
    [InlineData("Plugins/OpenApi/instacart-service.yaml",
        "Instacart",
        "create",
        """{"title":"Shopping List", "ingredients": ["Flour"], "question": "what ingredients do I need to make chocolate cookies?", "partner_name": "OpenAI" }"""
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

        // note that this plugin is not compliant according to the underlying validator in SK
        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            name,
            pluginFilePath,
            new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });

        var arguments = new KernelArguments
        {
            ["payload"] = payload
        };

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }

    [Theory]
    [InlineData("Plugins/OpenApi/instacart-service.yaml", "Instacart", "create")]
    public async Task QueryInstacartPluginWithDynamicPayloadAsync(
        string pluginFilePath,
        string name,
        string functionName)
    {
        // Arrange
        using var stream = System.IO.File.OpenRead(pluginFilePath);
        using HttpClient httpClient = new();
        var kernel = new Kernel();

        // note that this plugin is not compliant according to the underlying validator in SK
        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            name,
            stream,
            new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = true });

        var arguments = new KernelArguments
        {
            ["title"] = "Shopping List",
            ["ingredients"] = new string[] { "Flour", "Sugar", "Eggs" },
            ["instructions"] = new string[] { "Cream softened butter and granulated sugar", "Add eggs one at a time, mix well, and stir in vanilla extract", "Combine dry ingredients and mix" },
            ["question"] = "what ingredients do I need to make chocolate cookies?",
            ["partner_name"] = "OpenAI"
        };

        // Act
        await plugin[functionName].InvokeAsync(kernel, arguments);
    }
}
