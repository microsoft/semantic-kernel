// Copyright (c) Microsoft. All rights reserved.

using MCPServer.Tools;
using Microsoft.SemanticKernel;
using ModelContextProtocol;

// Create a kernel builder and add plugins
IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.Plugins.AddFromType<DateTimeUtils>();
kernelBuilder.Plugins.AddFromType<WeatherUtils>();

// Build the kernel
Kernel kernel = kernelBuilder.Build();

var builder = Host.CreateEmptyApplicationBuilder(settings: null);
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    // Add kernel functions to the MCP server as MCP tools
    .WithTools(kernel.Plugins.SelectMany(p => p.Select(f => f.AsAIFunction())));
await builder.Build().RunAsync();
