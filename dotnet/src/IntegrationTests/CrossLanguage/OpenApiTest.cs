// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
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
    private readonly JsonNode? _expectedJson;

    public OpenApiTest()
    {
        string expectedData = File.ReadAllText("./CrossLanguage/Data/LightBulbApiTest.json");
        this._expectedJson = JsonNode.Parse(expectedData);
    }

    [Fact]
    public async Task GetLightsAsync()
    {
        const string Operation = "GetLights";

        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync(Operation, new()
        {
            { "roomId", "1" }
        });

        this.AssertMethodAndUri(Operation, httpMessageHandlerStub);
    }

    [Fact]
    public async Task GetLightByIdAsync()
    {
        const string Operation = "GetLightById";

        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync(Operation, new()
        {
            { "id", "1" }
        });

        this.AssertMethodAndUri(Operation, httpMessageHandlerStub);
    }

    [Fact]
    public async Task DeleteLightByIdAsync()
    {
        const string Operation = "DeleteLightById";

        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync(Operation, new()
        {
            { "id", "1" }
        });

        this.AssertMethodAndUri(Operation, httpMessageHandlerStub);
    }

    [Fact]
    public async Task CreateLightsAsync()
    {
        const string Operation = "CreateLights";

        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync(Operation, new()
        {
            { "roomId", "1" },
            { "lightName", "disco" }
        });

        this.AssertMethodAndUri(Operation, httpMessageHandlerStub);
    }

    [Fact]
    public async Task PutLightByIdAsync()
    {
        const string Operation = "PutLightById";

        using var httpMessageHandlerStub = await this.SetUpOpenApiFunctionCallAsync(Operation, new()
        {
            { "id", "1" },
            { "hexColor", "11EE11" }
        });

        this.AssertMethodAndUri(Operation, httpMessageHandlerStub);

        string? contentType = this._expectedJson?[Operation]?["ContentType"]?.ToString();
        Assert.NotNull(contentType);
        Assert.True(httpMessageHandlerStub?.ContentHeaders?.ContentType?.ToString().StartsWith(contentType, System.StringComparison.InvariantCulture));

        string requestBody = System.Text.Encoding.UTF8.GetString(httpMessageHandlerStub?.RequestContent ?? Array.Empty<byte>());
        JsonNode? obtainedObject = JsonNode.Parse(requestBody);
        Assert.NotNull(obtainedObject);

        Assert.True(JsonNode.DeepEquals(obtainedObject, this._expectedJson?[Operation]?["Body"]));
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

    private void AssertMethodAndUri(string operation, HttpMessageHandlerStub httpMessageHandlerStub)
    {
        Assert.Equal(this._expectedJson?[operation]?["Method"]?.ToString(), httpMessageHandlerStub?.Method?.ToString());
        Assert.Equal(this._expectedJson?[operation]?["Uri"]?.ToString(), httpMessageHandlerStub?.RequestUri?.ToString());
    }
}
