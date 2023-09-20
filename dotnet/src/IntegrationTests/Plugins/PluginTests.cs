// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;
public class PluginTests
{
    [Theory]
    [InlineData("https://www.klarna.com/.well-known/ai-plugin.json", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    [InlineData("https://www.klarna.com/us/shopping/public/openai/v0/api-docs/", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    public async Task QueryKlarnaPluginAsync(
        string pluginEndpoint,
        string name,
        string functionName,
        string query,
        int size,
        int budget,
        string countryCode)
    {
        // Arrange
        var kernel = new KernelBuilder().Build();
        using HttpClient httpClient = new();

        var skill = await kernel.ImportAIPluginAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiPluginExecutionParameters(httpClient));

        var contextVariables = new ContextVariables();
        contextVariables["q"] = query;
        contextVariables["size"] = size.ToString(System.Globalization.CultureInfo.InvariantCulture);
        contextVariables["budget"] = budget.ToString(System.Globalization.CultureInfo.InvariantCulture);
        contextVariables["countryCode"] = countryCode;

        // Act
        await skill[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
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
        var kernel = new KernelBuilder().Build();
        using HttpClient httpClient = new();

        //note that this plugin is not compliant according to the underlying validator in SK
        var skill = await kernel.ImportAIPluginAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiPluginExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

        var contextVariables = new ContextVariables();
        contextVariables["payload"] = payload;

        // Act
        await skill[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
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
            var kernel = new KernelBuilder().Build();
            using HttpClient httpClient = new();

            //note that this plugin is not compliant according to the underlying validator in SK
            var skill = await kernel.ImportAIPluginAsync(
                name,
                stream,
                new OpenApiPluginExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

            var contextVariables = new ContextVariables();
            contextVariables["payload"] = payload;

            // Act
            await skill[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
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
        var kernel = new KernelBuilder().Build();
        using HttpClient httpClient = new();

        //note that this plugin is not compliant according to the underlying validator in SK
        var skill = await kernel.ImportAIPluginAsync(
            name,
            pluginFilePath,
            new OpenApiPluginExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

        var contextVariables = new ContextVariables();
        contextVariables["payload"] = payload;

        // Act
        await skill[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
    }
}
