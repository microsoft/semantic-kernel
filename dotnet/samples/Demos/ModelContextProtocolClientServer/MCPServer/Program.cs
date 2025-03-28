// Copyright (c) Microsoft. All rights reserved.

using Azure.Monitor.OpenTelemetry.Exporter;
using MCPServer;
using Microsoft.SemanticKernel;
using ModelContextProtocol;
using OpenTelemetry.Resources;
using OpenTelemetry;
using OpenTelemetry.Trace;
using OpenTelemetry.Metrics;
using MCPServer.Resources;

// Enable Application Insights telemetry
string connectionString = GetAppInsightsConnectionString();

// Enable diagnostics with sensitive data.
AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

var resourceBuilder = ResourceBuilder
    .CreateDefault()
    .AddService("SKTelemetry");

using var traceProvider = Sdk.CreateTracerProviderBuilder()
    .SetResourceBuilder(resourceBuilder)
    .AddSource("Microsoft.SemanticKernel*")
    .AddAzureMonitorTraceExporter(options => options.ConnectionString = connectionString)
    .Build();

using var meterProvider = Sdk.CreateMeterProviderBuilder()
    .SetResourceBuilder(resourceBuilder)
    .AddMeter("Microsoft.SemanticKernel*")
    .AddAzureMonitorMetricExporter(options => options.ConnectionString = connectionString)
    .Build();

using var loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddOpenTelemetry(options =>
    {
        options.SetResourceBuilder(resourceBuilder);
        options.AddAzureMonitorLogExporter(options => options.ConnectionString = connectionString);
        options.IncludeFormattedMessage = true;
        options.IncludeScopes = true;
    });
    builder.AddFilter("Microsoft.SemanticKernel*", LogLevel.Trace);
});

// Build the kernel
IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.Services.AddSingleton<ILoggerFactory>(loggerFactory);

Kernel kernel = kernelBuilder.Build();

// Import a OpenAPI plugin defined weather.json OpenAPI/Swagger spec
using Stream stream = EmbeddedResource.ReadAsStream("weather.json");
await kernel.ImportPluginFromOpenApiAsync("Weather", stream);

// Register a function invocation filter to validate function calls
kernel.AutoFunctionInvocationFilters.Add(new ContentSafetyAutoFunctionInvocationFilter());

var builder = Host.CreateEmptyApplicationBuilder(settings: null);
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    // Add kernel functions to the MCP server as MCP tools
    .WithTools(kernel.Plugins.SelectMany(p => p.Select(f => f.AsAIFunction())));
await builder.Build().RunAsync();

static string GetAppInsightsConnectionString()
{
    var config = new ConfigurationBuilder()
        .AddUserSecrets<Program>()
        .AddEnvironmentVariables()
        .Build();

    return config["ApplicationInsights:ConnectionString"]!;
}
