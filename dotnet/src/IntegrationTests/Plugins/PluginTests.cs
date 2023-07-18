// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;
public class PluginTests
{
    [Theory]
    [InlineData("https://www.klarna.com/.well-known/ai-plugin.json", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    [InlineData("https://www.klarna.com/us/shopping/public/openai/v0/api-docs/", "Klarna", "productsUsingGET", "Laptop", 3, 200, "US")]
    public async Task QueryKlarnaViaChatGPTPlugin(
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
            new OpenApiSkillExecutionParameters(httpClient));

        var contextVariables = new ContextVariables();
        contextVariables["q"] = query;
        contextVariables["size"] = size.ToString();
        contextVariables["budget"] = budget.ToString();
        contextVariables["countryCode"] = countryCode;

        // Act
        var result = await skill[functionName].InvokeAsync(new SKContext(contextVariables));

        // Assert
        Assert.False(result.ErrorOccurred);
    }
}
