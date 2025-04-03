// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using MCPServer;
using MCPServer.Prompts;
using MCPServer.Tools;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;

// Create a kernel builder and add plugins
IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.Plugins.AddFromType<DateTimeUtils>();
kernelBuilder.Plugins.AddFromType<WeatherUtils>();

// Build the kernel
Kernel kernel = kernelBuilder.Build();

// Register prompts
PromptRegistry.RegisterPrompt(PromptDefinition.Create(EmbeddedResource.ReadAsString("getCurrentWeatherForCity.json"), kernel));

Debugger.Break();

var builder = Host.CreateEmptyApplicationBuilder(settings: null);
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly()

    // Add all functions from the kernel plugins to the MCP server as tools
    .WithTools(kernel.Plugins)

    .AddResourceTemplate(
        template: new() { UriTemplate = "doc://{type}/{filename}", Name = "test-template-name" },
        handler: async (context, arguments, services, cancellationToken) =>
        {
            // Simulate some processing
            await Task.Delay(1000, cancellationToken);

            // Return a dummy resource
            return new ReadResourceResult()
            {
                Contents = new List<ResourceContents>()
                {
                    new TextResourceContents()
                    {
                        Uri = "doc://test/test.txt",
                        MimeType = "text/plain",
                    }
                },
            };
        }
    )

    // Register prompt handlers
    .WithListPromptsHandler(PromptRegistry.HandlerListPromptRequestsAsync)
    .WithGetPromptHandler(PromptRegistry.HandlerGetPromptRequestsAsync);

    // Register resource handlers
    //.WithListResourceTemplatesHandler(ResourceRegistry.HandleListResourceTemplatesRequestAsync)
    //.WithListResourcesHandler(ResourceRegistry.HandleListResourcesRequestAsync)
    //.WithReadResourceHandler(ResourceRegistry.HandleReadResourceRequestAsync);

await builder.Build().RunAsync();
