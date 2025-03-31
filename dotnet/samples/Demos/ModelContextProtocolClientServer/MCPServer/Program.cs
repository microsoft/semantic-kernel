// Copyright (c) Microsoft. All rights reserved.

using MCPServer;
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
    // Add all functions from the kernel plugins to the MCP server as tools
    .WithTools(kernel.Plugins);
await builder.Build().RunAsync();
