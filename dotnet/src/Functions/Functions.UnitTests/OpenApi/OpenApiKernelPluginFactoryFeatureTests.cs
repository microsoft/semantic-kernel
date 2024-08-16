// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class OpenApiKernelPluginFactoryFeatureTests
{
    [Fact]
    public async Task ItShouldCreatePluginWithOperationPayloadForAnyOfSchemaAsync()
    {
        await using var openApiDocument = ResourcePluginsProvider.LoadFromResource("openapi_feature_testsV3_0.json");

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, executionParameters: new OpenApiFunctionExecutionParameters { EnableDynamicPayload = false });

        var postFoobarFunction = plugin["AnyOfPost"];
        Assert.NotNull(postFoobarFunction);

        var functionView = postFoobarFunction.Metadata;
        Assert.NotNull(functionView);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal(JsonValueKind.Array, payloadParameter.Schema!.RootElement.GetProperty("anyOf").ValueKind);
    }

    [Fact]
    public async Task ItShouldCreatePluginWithOperationPayloadForAllOfSchemaAsync()
    {
        await using var openApiDocument = ResourcePluginsProvider.LoadFromResource("openapi_feature_testsV3_0.json");
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, executionParameters: new OpenApiFunctionExecutionParameters { EnableDynamicPayload = false });

        var postFoobarFunction = plugin["AllOfPost"];
        Assert.NotNull(postFoobarFunction);

        var functionView = postFoobarFunction.Metadata;
        Assert.NotNull(functionView);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal(JsonValueKind.Array, payloadParameter.Schema!.RootElement.GetProperty("allOf").ValueKind);
    }

    [Fact]
    public async Task ItShouldCreatePluginWithOperationPayloadForOneOfSchemaAsync()
    {
        await using var openApiDocument = ResourcePluginsProvider.LoadFromResource("openapi_feature_testsV3_0.json");

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, executionParameters: new OpenApiFunctionExecutionParameters { EnableDynamicPayload = false });

        var postFoobarFunction = plugin["OneOfPost"];
        Assert.NotNull(postFoobarFunction);

        var functionView = postFoobarFunction.Metadata;
        Assert.NotNull(functionView);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal(JsonValueKind.Array, payloadParameter.Schema!.RootElement.GetProperty("oneOf").ValueKind);
    }
}
