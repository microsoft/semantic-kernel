// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// Examples to show how to create plugins from OpenAPI specs.
/// </summary>
public class CreatePluginFromOpenApiSpec_Github(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Example to show how to consume operation extensions and other metadata from an OpenAPI spec.
    /// Try modifying the sample schema to simulate the other cases by
    /// 1. Changing the value of x-openai-isConsequential to true and see how the function execution is skipped.
    /// 2. Removing the x-openai-isConsequential property and see how the function execution is skipped.
    /// </summary>
    [Fact]
    public async Task RunOpenAIPluginWithMetadataAsync()
    {
        Kernel kernel = new();

        // This HTTP client is optional. SK will fallback to a default internal one if omitted.
        using HttpClient httpClient = new();

        // Create a sample OpenAPI schema that calls the github versions api, and has an operation extension property.
        // The x-openai-isConsequential property is the operation extension property.
        var schema = """
            {
                "openapi": "3.0.1",
                "info": {
                    "title": "Github Versions API",
                    "version": "1.0.0"
                },
                "servers": [ { "url": "https://api.github.com" } ],
                "paths": {
                    "/versions": {
                        "get": {
                            "x-openai-isConsequential": false,
                            "operationId": "getVersions",
                            "responses": {
                                "200": {
                                    "description": "OK"
                                }
                            }
                        }
                    }
                }
            }
            """;
        var schemaStream = new MemoryStream();
        WriteStringToStream(schemaStream, schema);

        // Import an Open API plugin from a stream.
        var plugin = await kernel.CreatePluginFromOpenApiAsync("GithubVersionsApi", schemaStream, new OpenApiFunctionExecutionParameters(httpClient));

        // Get the function to be invoked and its metadata and extension properties.
        var function = plugin["getVersions"];
        function.Metadata.AdditionalProperties.TryGetValue("operation-extensions", out var extensionsObject);
        var operationExtensions = extensionsObject as Dictionary<string, object?>;

        // *******************************************************************************************************************************
        // ******* Use case 1: Consume the x-openai-isConsequential extension value to determine if the function has consequences  *******
        // ******* and only invoke the function if it is consequence free.                                                         *******
        // *******************************************************************************************************************************
        if (operationExtensions is null || !operationExtensions.TryGetValue("x-openai-isConsequential", out var isConsequential) || isConsequential is null)
        {
            Console.WriteLine("We cannot determine if the function has consequences, since the isConsequential extension is not provided, so safer not to run it.");
        }
        else if ((isConsequential as bool?) == true)
        {
            Console.WriteLine("This function may have unwanted consequences, so safer not to run it.");
        }
        else
        {
            // Invoke the function and output the result.
            var functionResult = await kernel.InvokeAsync(function);
            var result = functionResult.GetValue<RestApiOperationResponse>();
            Console.WriteLine($"Function execution result: {result?.Content}");
        }

        // *******************************************************************************************************************************
        // ******* Use case 2: Consume the http method type to determine if this is a read or write operation and only execute if  *******
        // ******* it is a read operation.                                                                                         *******
        // *******************************************************************************************************************************
        if (function.Metadata.AdditionalProperties.TryGetValue("method", out var method) && method as string is "GET")
        {
            // Invoke the function and output the result.
            var functionResult = await kernel.InvokeAsync(function);
            var result = functionResult.GetValue<RestApiOperationResponse>();
            Console.WriteLine($"Function execution result: {result?.Content}");
        }
        else
        {
            Console.WriteLine("This is a write operation, so safer not to run it.");
        }
    }

    private static void WriteStringToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }
}
