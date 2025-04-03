// Copyright (c) Microsoft. All rights reserved.

using MCPServer;
using MCPServer.Prompts;
using MCPServer.Tools;
using Microsoft.SemanticKernel;

// Create a kernel builder and add plugins
IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.Plugins.AddFromType<DateTimeUtils>();
kernelBuilder.Plugins.AddFromType<WeatherUtils>();

// Build the kernel
Kernel kernel = kernelBuilder.Build();

// Register prompts
PromptRegistry.RegisterPrompt(PromptDefinition.Create(EmbeddedResource.ReadAsString("getCurrentWeatherForCity.json"), kernel));

var builder = Host.CreateEmptyApplicationBuilder(settings: null);
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    // Add all functions from the kernel plugins to the MCP server as tools
    .WithTools(kernel.Plugins)
    // Register prompt handlers
    .WithListPromptsHandler(PromptRegistry.HandlerListPromptRequestsAsync)
    .WithGetPromptHandler(PromptRegistry.HandlerGetPromptRequestsAsync);
await builder.Build().RunAsync();
