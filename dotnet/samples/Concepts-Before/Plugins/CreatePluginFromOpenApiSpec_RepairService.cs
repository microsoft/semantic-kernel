// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// Sample shows how to create a <see cref="KernelPlugin"/> from an Open API manifest.
/// </summary>
public sealed class CreatePluginFromOpenApiSpec_RepairService(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ShowCreatingRepairServicePluginAsync()
    {
        // Arrange
        var kernel = new Kernel();
        using var stream = System.IO.File.OpenRead("Resources/Plugins/RepairServicePlugin/repair-service.json");
        using HttpClient httpClient = new();

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync(
            "RepairService",
            stream,
            new OpenApiFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });
        kernel.Plugins.Add(plugin);

        var arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Engine oil change", "description": "Need to drain the old engine oil and replace it with fresh oil.", "assignedTo": "", "date": "", "image": "" }"""
        };

        // Create Repair
        var result = await plugin["createRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(result.ToString());

        // List All Repairs
        result = await plugin["listRepairs"].InvokeAsync(kernel, arguments);
        var repairs = JsonSerializer.Deserialize<Repair[]>(result.ToString());
        Assert.True(repairs?.Length > 0);
        var id = repairs[repairs.Length - 1].Id;

        // Update Repair
        arguments = new KernelArguments
        {
            ["payload"] = $"{{ \"id\": {id}, \"assignedTo\": \"Karin Blair\", \"date\": \"2024-04-16\", \"image\": \"https://www.howmuchisit.org/wp-content/uploads/2011/01/oil-change.jpg\" }}"
        };

        result = await plugin["updateRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(result.ToString());

        // Delete Repair
        arguments = new KernelArguments
        {
            ["payload"] = $"{{ \"id\": {id} }}"
        };

        result = await plugin["deleteRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(result.ToString());
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
