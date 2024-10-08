// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// Sample shows how to register a custom HTTP content reader for an Open API plugin.
/// </summary>
public sealed class CustomHttpContentReaderForOpenApiPlugin(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ShowReadingJsonAsStreamAsync()
    {
        var kernel = new Kernel();

        // Register the custom HTTP content reader
        var executionParameters = new OpenApiFunctionExecutionParameters() { HttpResponseContentReader = ReadHttpResponseContentAsync };

        // Create OpenAPI plugin
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("RepairService", "Resources/Plugins/RepairServicePlugin/repair-service.json", executionParameters);

        // Create a repair so it can be read as a stream in the following step
        var arguments = new KernelArguments
        {
            ["title"] = "The Case of the Broken Gizmo",
            ["description"] = "It's broken. Send help!",
            ["assignedTo"] = "Tech Magician"
        };
        var createResult = await plugin["createRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(createResult.ToString());

        // List relevant repairs
        arguments = new KernelArguments
        {
            ["assignedTo"] = "Tech Magician"
        };
        var listResult = await plugin["listRepairs"].InvokeAsync(kernel, arguments);
        using var reader = new StreamReader((Stream)listResult.GetValue<RestApiOperationResponse>()!.Content!);
        var content = await reader.ReadToEndAsync();
        var repairs = JsonSerializer.Deserialize<Repair[]>(content);
        Console.WriteLine(content);

        // Delete the repair
        arguments = new KernelArguments
        {
            ["id"] = repairs!.Where(r => r.AssignedTo == "Tech Magician").First().Id.ToString()
        };
        var deleteResult = await plugin["deleteRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(deleteResult.ToString());
    }

    /// <summary>
    /// A custom HTTP content reader to change the default behavior of reading HTTP content.
    /// </summary>
    /// <param name="context">The HTTP response content reader context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The HTTP response content.</returns>
    private static async Task<object?> ReadHttpResponseContentAsync(HttpResponseContentReaderContext context, CancellationToken cancellationToken)
    {
        // Read JSON content as a stream rather than as a string, which is the default behavior
        if (context.Response.Content.Headers.ContentType?.MediaType == "application/json")
        {
            return await context.Response.Content.ReadAsStreamAsync(cancellationToken);
        }

        // HTTP request and response properties can be used to decide how to read the content.
        // The 'if' operator below is not relevant to the current example and is just for demonstration purposes.
        if (context.Request.Headers.Contains("x-stream"))
        {
            return await context.Response.Content.ReadAsStreamAsync(cancellationToken);
        }

        // Return null to indicate that any other HTTP content not handled above should be read by the default reader.
        return null;
    }

    private sealed class Repair
    {
        [JsonPropertyName("id")]
        public int? Id { get; set; }

        [JsonPropertyName("title")]
        public string? Title { get; set; }

        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("assignedTo")]
        public string? AssignedTo { get; set; }

        [JsonPropertyName("date")]
        public string? Date { get; set; }

        [JsonPropertyName("image")]
        public string? Image { get; set; }
    }
}
