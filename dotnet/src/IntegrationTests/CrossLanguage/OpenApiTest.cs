// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

public class OpenApiTest
{
    [Fact]
    public async Task GetLightsAsync()
    {
        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync("GetLights", new()
        {
            { "roomId", "1" }
        });

        Assert.Equal(HttpMethod.Get, httpMessageHandlerStub.Method);
        Assert.Equal("https://127.0.0.1/Lights?roomId=1", httpMessageHandlerStub?.RequestUri?.ToString());
    }

    [Fact]
    public async Task GetLightByIdAsync()
    {
        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync("GetLightById", new()
        {
            { "id", "1" }
        });

        Assert.Equal(HttpMethod.Get, httpMessageHandlerStub.Method);
        Assert.Equal("https://127.0.0.1/Lights/1", httpMessageHandlerStub?.RequestUri?.ToString());
    }

    [Fact]
    public async Task DeleteLightByIdAsync()
    {
        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync("DeleteLightById", new()
        {
            { "id", "1" }
        });

        Assert.Equal(HttpMethod.Delete, httpMessageHandlerStub.Method);
        Assert.Equal("https://127.0.0.1/Lights/1", httpMessageHandlerStub?.RequestUri?.ToString());
    }

    [Fact]
    public async Task CreateLightsAsync()
    {
        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync("CreateLights", new()
        {
            { "roomId", "1" },
            { "lightName", "disco" }
        });

        Assert.Equal(HttpMethod.Post, httpMessageHandlerStub.Method);
        Assert.Equal("https://127.0.0.1/Lights?roomId=1&lightName=disco", httpMessageHandlerStub?.RequestUri?.ToString());
    }

    [Fact]
    public async Task PutLightByIdAsync()
    {
        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync("PutLightById", new()
        {
            { "id", "1" },
            { "hexColor", "11EE11" }
        });

        Assert.Equal(HttpMethod.Put, httpMessageHandlerStub.Method);
        Assert.True(httpMessageHandlerStub?.ContentHeaders?.ContentType?.ToString().StartsWith("application/json", System.StringComparison.InvariantCulture));
        Assert.Equal("https://127.0.0.1/Lights/1", httpMessageHandlerStub?.RequestUri?.ToString());

        string content = System.Text.Encoding.UTF8.GetString(httpMessageHandlerStub?.RequestContent ?? Array.Empty<byte>());
        JsonNode? obtainedObject = JsonNode.Parse(content);
        Assert.NotNull(obtainedObject);

        JsonNode? expectedObject = JsonNode.Parse("{\"hexColor\": \"11EE11\"}");
        Assert.NotNull(expectedObject);

        Assert.True(JsonNode.DeepEquals(obtainedObject, expectedObject));
    }

    private async Task<HttpMessageHandlerStub> SetUpOpenApiFunctionCallAsync(string functionName, KernelArguments args)
    {
        using var kernelProvider = new KernelRequestTracer();
        Kernel kernel = kernelProvider.GetNewKernel();

        using var httpMessageHandlerStub = new HttpMessageHandlerStub();
        var execParams = new OpenApiFunctionExecutionParameters { HttpClient = new HttpClient(httpMessageHandlerStub) };
        var plugin = await kernel.CreatePluginFromOpenApiAsync("LightBulb", "./CrossLanguage/Data/LightBulbApi.json", execParams);

        KernelFunction function = plugin[functionName];

        await KernelRequestTracer.RunFunctionAsync(kernel, isStreaming: false, function, args);

        return httpMessageHandlerStub;
    }
}
