// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// Sample with demonstration of logging in OpenAPI plugins.
/// </summary>
public sealed class OpenApiPlugin_Telemetry(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Default logging in OpenAPI plugins.
    /// It's possible to use HTTP logging middleware in ASP.NET applications to log information about HTTP request, headers, body, response etc.
    /// More information here: <see href="https://learn.microsoft.com/en-us/aspnet/core/fundamentals/http-logging"/>.
    /// For custom logging logic, use <see cref="DelegatingHandler"/>.
    /// More information here: <see href="https://learn.microsoft.com/en-us/aspnet/web-api/overview/advanced/http-message-handlers"/>.
    /// </summary>
    [Fact]
    public async Task LoggingAsync()
    {
        // Arrange
        using var stream = File.OpenRead("Resources/Plugins/RepairServicePlugin/repair-service.json");
        using HttpClient httpClient = new();

        var kernelBuilder = Kernel.CreateBuilder();

        // If ILoggerFactory is registered in kernel's DI container, it will be used for logging purposes in OpenAPI functionality.
        kernelBuilder.Services.AddSingleton<ILoggerFactory>(this.LoggerFactory);

        var kernel = kernelBuilder.Build();

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync(
            "RepairService",
            stream,
            new OpenApiFunctionExecutionParameters(httpClient)
            {
                IgnoreNonCompliantErrors = true,
                EnableDynamicPayload = false,
                // For non-DI scenarios, it's possible to set ILoggerFactory in execution parameters when creating a plugin.
                // If ILoggerFactory is provided in both ways through the kernel's DI container and execution parameters,
                // the one from execution parameters will be used.
                LoggerFactory = kernel.LoggerFactory
            });

        kernel.Plugins.Add(plugin);

        var arguments = new KernelArguments
        {
            ["payload"] = """{ "title": "Engine oil change", "description": "Need to drain the old engine oil and replace it with fresh oil.", "assignedTo": "", "date": "", "image": "" }""",
            ["content-type"] = "application/json"
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
            ["payload"] = $"{{ \"id\": {id}, \"assignedTo\": \"Karin Blair\", \"date\": \"2024-04-16\", \"image\": \"https://www.howmuchisit.org/wp-content/uploads/2011/01/oil-change.jpg\" }}",
            ["content-type"] = "application/json"
        };

        result = await plugin["updateRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(result.ToString());

        // Delete Repair
        arguments = new KernelArguments
        {
            ["payload"] = $"{{ \"id\": {id} }}",
            ["content-type"] = "application/json"
        };

        result = await plugin["deleteRepair"].InvokeAsync(kernel, arguments);
        Console.WriteLine(result.ToString());

        // Output:
        // Registering Rest function RepairService.listRepairs
        // Created KernelFunction 'listRepairs' for '<CreateRestApiFunction>g__ExecuteAsync|0'
        // Registering Rest function RepairService.createRepair
        // Created KernelFunction 'createRepair' for '<CreateRestApiFunction>g__ExecuteAsync|0'
        // Registering Rest function RepairService.updateRepair
        // Created KernelFunction 'updateRepair' for '<CreateRestApiFunction>g__ExecuteAsync|0'
        // Registering Rest function RepairService.deleteRepair
        // Created KernelFunction 'deleteRepair' for '<CreateRestApiFunction>g__ExecuteAsync|0'
        // Function RepairService - createRepair invoking.
        // Function RepairService - createRepair arguments: { "payload":"{ \u0022title\u0022: \u0022Engine oil change...
        // Function RepairService-createRepair succeeded.
        // Function RepairService-createRepair result: { "Content":"New repair created",...
        // Function RepairService-createRepair completed. Duration: 0.2793481s
        // New repair created
        // Function RepairService-listRepairs invoking.
        // Function RepairService-listRepairs arguments: { "payload":"{ \u0022title\u0022: \u0022Engine oil change...
        // Function RepairService-listRepairs succeeded.
        // Function RepairService-listRepairs result: { "Content":"[{\u0022id\u0022:79,\u0022title...
        // Function RepairService - updateRepair invoking.
        // Function RepairService-updateRepair arguments: { "payload":"{ \u0022id\u0022: 96, ...
        // Function RepairService-updateRepair succeeded.
        // Function RepairService-updateRepair result: { "Content":"Repair updated",...
        // Function RepairService-updateRepair completed. Duration: 0.0430169s
        // Repair updated
        // Function RepairService - deleteRepair invoking.
        // Function RepairService-deleteRepair arguments: { "payload":"{ \u0022id\u0022: 96 ...
        // Function RepairService-deleteRepair succeeded.
        // Function RepairService-deleteRepair result: { "Content":"Repair deleted",...
        // Function RepairService-deleteRepair completed. Duration: 0.049715s
        // Repair deleted
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
