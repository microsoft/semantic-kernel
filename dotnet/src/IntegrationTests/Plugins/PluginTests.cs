// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;
public class PluginTests
{
    private static async Task AuthenticateRequestAsync(HttpRequestMessage request, OpenAIManifestAuthenticationConfig? authConfig = null)
    {
        if (authConfig?.Type == OpenAIAuthenticationType.OAuth)
        {
            var clientId = "CLIENT_ID";
            var clientSecret = "CLIENT_SECRET";

            using var content = new FormUrlEncodedContent(new KeyValuePair<string, string>[] {
                new("client_id", clientId),
                new("client_secret", clientSecret),
                new("scope", authConfig!.Scope ?? ""),
                new("grant_type", "client_credentials"),
            });

            using var client = new HttpClient();
            var response = await client.PostAsync(authConfig.AuthorizationUrl, content);

            if (response.IsSuccessStatusCode)
            {
                var tokenResponse = JsonNode.Parse(await response.Content.ReadAsStringAsync());
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", tokenResponse?["access_token"]?.ToString());
            }
            else
            {
                Assert.Fail("Error acquiring access token: " + response.ReasonPhrase);
            }
        }
    }

    [Theory]
    [InlineData("https://localhost:40443/.well-known/ai-plugin.json", "AzureKeyVault", "SetSecret", "https://dehoward-test-kv.vault.azure.net/", "dehoward-foo", "bar")]
    [InlineData("https://localhost:40443/.well-known/ai-plugin.json", "AzureKeyVault", "GetSecret", "https://dehoward-test-kv.vault.azure.net/", "dehoward-foo", "bar")]
    public async Task QueryAzureKeyVaultAsync(
        string pluginEndpoint,
        string name,
        string functionName,
        string keyVaultEndpoint,
        string secretName,
        string? secretValue = null)
    {
        // Arrange
        var kernel = new KernelBuilder().Build();
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFunctionsAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiFunctionExecutionParameters { AuthCallback = AuthenticateRequestAsync, EnableDynamicPayload = true });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("server-url", keyVaultEndpoint);
        contextVariables.Set("secret-name", secretName);
        contextVariables.Set("value", secretValue);
        contextVariables.Set("api-version", "7.0");
        contextVariables.Set("enabled", "true");

        // Act
        var kernelResult = await kernel.RunAsync(contextVariables, plugin[functionName]);

        // Assert
        var result = kernelResult.GetValue<RestApiOperationResponse>();
        Assert.NotNull(result);

        var content = JsonSerializer.Deserialize<JsonNode>(result!.Content.ToString()!);
        Assert.Equal(secretValue, content!["value"]!.ToString()!);
    }

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

        var plugin = await kernel.ImportPluginFunctionsAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiFunctionExecutionParameters(httpClient));

        var contextVariables = new ContextVariables();
        contextVariables["q"] = query;
        contextVariables["size"] = size.ToString(System.Globalization.CultureInfo.InvariantCulture);
        contextVariables["budget"] = budget.ToString(System.Globalization.CultureInfo.InvariantCulture);
        contextVariables["countryCode"] = countryCode;

        // Act
        await plugin[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
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
        var plugin = await kernel.ImportPluginFunctionsAsync(
            name,
            new Uri(pluginEndpoint),
            new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

        var contextVariables = new ContextVariables();
        contextVariables["payload"] = payload;

        // Act
        await plugin[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
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
            var plugin = await kernel.ImportPluginFunctionsAsync(
                name,
                stream,
                new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

            var contextVariables = new ContextVariables();
            contextVariables["payload"] = payload;

            // Act
            await plugin[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
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
        var plugin = await kernel.ImportPluginFunctionsAsync(
            name,
            pluginFilePath,
            new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true });

        var contextVariables = new ContextVariables();
        contextVariables["payload"] = payload;

        // Act
        await plugin[functionName].InvokeAsync(kernel.CreateNewContext(contextVariables));
    }
}
