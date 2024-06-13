// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;

public class RepairServiceTests
{
    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateInvokingRepairServicePluginAsync()
    {
        // Arrange
        var kernel = new Kernel();
        using var stream = System.IO.File.OpenRead("Plugins/repair-service.json");
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            "RepairService",
            stream,
            new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });

        var arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Engine oil change", "description": "Need to drain the old engine oil and replace it with fresh oil.", "assignedTo": "", "date": "", "image": "" }"""
        };

        // Create Repair
        var result = await plugin["createRepair"].InvokeAsync(kernel, arguments);

        Assert.NotNull(result);
        Assert.Equal("New repair created", result.ToString());

        // List All Repairs
        result = await plugin["listRepairs"].InvokeAsync(kernel);

        Assert.NotNull(result);
        var repairs = JsonSerializer.Deserialize<Repair[]>(result.ToString());
        Assert.True(repairs?.Length > 0);

        var id = repairs[repairs.Length - 1].Id;

        // Update Repair
        arguments = new KernelArguments
        {
            ["payload"] = $"{{ \"id\": {id}, \"assignedTo\": \"Karin Blair\", \"date\": \"2024-04-16\", \"image\": \"https://www.howmuchisit.org/wp-content/uploads/2011/01/oil-change.jpg\" }}"
        };

        result = await plugin["updateRepair"].InvokeAsync(kernel, arguments);

        Assert.NotNull(result);
        Assert.Equal("Repair updated", result.ToString());

        // Delete Repair
        arguments = new KernelArguments
        {
            ["payload"] = $"{{ \"id\": {id} }}"
        };

        result = await plugin["deleteRepair"].InvokeAsync(kernel, arguments);

        Assert.NotNull(result);
        Assert.Equal("Repair deleted", result.ToString());
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task HttpOperationExceptionIncludeRequestInfoAsync()
    {
        // Arrange
        var kernel = new Kernel();
        using var stream = System.IO.File.OpenRead("Plugins/repair-service.json");
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            "RepairService",
            stream,
            new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });

        var arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Engine oil change", "description": "Need to drain the old engine oil and replace it with fresh oil.", "assignedTo": "", "date": "", "image": "" }"""
        };

        var id = 99999;

        // Update Repair
        arguments = new KernelArguments
        {
            ["payload"] = $"{{ \"id\": {id}, \"assignedTo\": \"Karin Blair\", \"date\": \"2024-04-16\", \"image\": \"https://www.howmuchisit.org/wp-content/uploads/2011/01/oil-change.jpg\" }}"
        };

        try
        {
            await plugin["updateRepair"].InvokeAsync(kernel, arguments);
            Assert.Fail("Expected HttpOperationException");
        }
        catch (HttpOperationException ex)
        {
            Assert.Equal("Response status code does not indicate success: 404 (Not Found).", ex.Message);
            Assert.Equal("Patch", ex.Data["http.request.method"]);
            Assert.Equal("https://piercerepairsapi.azurewebsites.net/repairs", ex.Data["url.full"]);
        }
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task UseFilterToAssignNewRepairAsync()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.FunctionInvocationFilters.Add(new CreateRepairFilter());
        using var stream = System.IO.File.OpenRead("Plugins/repair-service.json");
        using HttpClient httpClient = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            "RepairService",
            stream,
            new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });

        // Create Repair - oil change
        var arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Engine oil change", "description": "Need to drain the old engine oil and replace it with fresh oil.", "assignedTo": "", "date": "", "image": "" }"""
        };
        var result = await plugin["createRepair"].InvokeAsync(kernel, arguments);

        Assert.NotNull(result);
        Assert.Equal("New repair created", result.ToString());

        // Create Repair - brake pads change
        arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Brake pads change", "description": "Need to replace the brake pads on all wheels.", "assignedTo": "", "date": "", "image": "" }"""
        };
        result = await plugin["createRepair"].InvokeAsync(kernel, arguments);

        Assert.NotNull(result);
        Assert.Equal("New repair created", result.ToString());

        // List All Repairs
        result = await plugin["listRepairs"].InvokeAsync(kernel);

        Assert.NotNull(result);
        var repairs = JsonSerializer.Deserialize<Repair[]>(result.ToString());
        Assert.True(repairs?.Length > 0);

        var id = repairs[repairs.Length - 1].Id;
    }

    public sealed class Repair
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

    public sealed class CreateRepairFilter() : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            if (context.Function.Name == "createRepair")
            {
                var payload = context.Arguments["payload"];
                var repair = JsonSerializer.Deserialize<Repair>(payload?.ToString() ?? string.Empty);
                if (repair is not null && string.IsNullOrEmpty(repair.AssignedTo))
                {
                    repair.Date = DateTime.UtcNow.ToString();
                    repair.AssignedTo = "Karin Blair";
                    context.Arguments["payload"] = JsonSerializer.Serialize(repair);
                }
            }

            await next(context);
        }
    }
}
