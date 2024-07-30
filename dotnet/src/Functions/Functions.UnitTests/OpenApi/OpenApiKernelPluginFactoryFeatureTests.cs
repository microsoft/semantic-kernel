// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class OpenApiKernelPluginFactoryFeatureTests
{
    [Fact]
    public async Task CreatesPluginWithOperationPayloadForAnyOfSchemaAsync()
    {
        await using var openApiDocument = ResourcePluginsProvider.LoadFromResource("openapi_any_of.json");

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, executionParameters: new OpenApiFunctionExecutionParameters{EnableDynamicPayload = false});

        var postFoobarFunction = plugin["PostFoobar"];
        Assert.NotNull(postFoobarFunction);

        var functionView = postFoobarFunction.Metadata;
        Assert.NotNull(functionView);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal(JsonValueKind.Array, payloadParameter.Schema!.RootElement.GetProperty("anyOf").ValueKind);
    }

    [Fact]
    public async Task CreatesPluginWithOperationPayloadForAllOfSchemaAsync()
    {
        await using var stream0 = ResourcePluginsProvider.LoadFromResource("openapi_any_of.json");
        // /components/schemas/fooBar
        await using var openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(stream0, (doc) =>
        {
            var schemas = doc["components"]!["schemas"]!;
            schemas["bar"]!["type"] = "object";
            schemas["bar"]!["properties"] = new JsonObject
            {
                ["name"] = new JsonObject
                {
                    ["type"] = "string"
                }
            };
            var anyOf = schemas["fooBar"]!["anyOf"];
            schemas["fooBar"]!["anyOf"] = null;
            var schema = new JsonObject
            {
                ["allOf"] = anyOf
            };
            schemas["fooBar"] = schema;
        });

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, executionParameters: new OpenApiFunctionExecutionParameters{EnableDynamicPayload = false});

        var postFoobarFunction = plugin["PostFoobar"];
        Assert.NotNull(postFoobarFunction);

        var functionView = postFoobarFunction.Metadata;
        Assert.NotNull(functionView);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal(JsonValueKind.Array, payloadParameter.Schema!.RootElement.GetProperty("allOf").ValueKind);
    }

    [Fact]
    public async Task CreatesPluginWithOperationPayloadForOneOfSchemaAsync()
    {
        await using var stream0 = ResourcePluginsProvider.LoadFromResource("openapi_any_of.json");
        // /components/schemas/fooBar
        await using var openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(stream0, (doc) =>
        {
            var schemas = doc["components"]!["schemas"]!;
            var anyOf = schemas["fooBar"]!["anyOf"];
            schemas["fooBar"]!["anyOf"] = null;
            var schema = new JsonObject
            {
                ["oneOf"] = anyOf
            };
            schemas["fooBar"] = schema;
        });

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, executionParameters: new OpenApiFunctionExecutionParameters{EnableDynamicPayload = false});

        var postFoobarFunction = plugin["PostFoobar"];
        Assert.NotNull(postFoobarFunction);

        var functionView = postFoobarFunction.Metadata;
        Assert.NotNull(functionView);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal(JsonValueKind.Array, payloadParameter.Schema!.RootElement.GetProperty("oneOf").ValueKind);
    }
}
