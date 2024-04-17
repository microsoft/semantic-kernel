// Copyright (c) Microsoft. All rights reserved.
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;

public class RepairServiceTests
{
    [Fact(Skip = "This test is for manual verification.")]
    public async Task RepairServicePluginAsync()
    {
        // Arrange
        var kernel = new Kernel();
        using var stream = System.IO.File.OpenRead("Plugins/repair-service.json");
        using HttpClient httpClient = new();

        //note that this plugin is not compliant according to the underlying validator in SK
        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            "RepairService",
            stream,
            new OpenAIFunctionExecutionParameters(httpClient) { IgnoreNonCompliantErrors = true, EnableDynamicPayload = false });

        var arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Engine oil change", "description": "Need to drain the old engine oil and replace it with fresh oil.", "assignedTo": "", "date": "", "image": "" }"""
        };

        // Act
        var result = await plugin["createRepair"].InvokeAsync(kernel, arguments);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("New repair created", result.ToString());

        arguments = new KernelArguments
        {
            ["payload"] = """{ "id": 1, "assignedTo": "Karin Blair", "date": "2024-04-16", "image": "https://www.howmuchisit.org/wp-content/uploads/2011/01/oil-change.jpg" }"""
        };

        // Act
        result = await plugin["updateRepair"].InvokeAsync(kernel, arguments);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Repair updated", result.ToString());

        arguments = new KernelArguments
        {
            ["payload"] = """{ "id": 1 }"""
        };

        // Act
        result = await plugin["deleteRepair"].InvokeAsync(kernel, arguments);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Repair deleted", result.ToString());
    }
}
