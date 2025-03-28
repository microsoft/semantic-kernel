// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol.Client;
using ModelContextProtocol.Configuration;
using ModelContextProtocol.Protocol.Transport;

IConfigurationRoot config = LoadConfiguration();

// Create an MCP client
await using var mcpClient = await McpClientFactory.CreateAsync(
    new McpServerConfig()
    {
        Id = "MCPServer",
        Name = "MCPServer",
        TransportType = TransportTypes.StdIo,
        TransportOptions = new()
        {
            // Point the client to the MCPServer server executable
            ["command"] = GetMCPServerPath()
        }
    },
    new McpClientOptions()
    {
        ClientInfo = new() { Name = "MCPClient", Version = "1.0.0" }
    }
 );

// Retrieve and display the list of tools available on the MCP server
Console.WriteLine("Available MCP tools:");
var tools = await mcpClient.GetAIFunctionsAsync().ConfigureAwait(false);
foreach (var tool in tools)
{
    Console.WriteLine($"\t{tool.Name}: {tool.Description}");
}

// Prepare and build kernel with the MCP tools as Kernel functions
var kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));
kernelBuilder.Services.AddOpenAIChatCompletion(serviceId: "openai", modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o-mini", apiKey: config["OpenAI:ApiKey"]!);

Kernel kernel = kernelBuilder.Build();

// Enable automatic function calling
OpenAIPromptExecutionSettings executionSettings = new()
{
    Temperature = 0,
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
};

// Execute a prompt using the MCP tools. The AI model will automatically call the appropriate MCP tools to answer the prompt.
var prompt = "What is the likely color of the sky in Seattle today?";
Console.WriteLine($"\nPrompt: {prompt}\n");

var result = await kernel.InvokePromptAsync(prompt, new(executionSettings)).ConfigureAwait(false);
Console.WriteLine($"Result: {result}");

Console.ReadKey();

static string GetMCPServerPath()
{
    // Determine the configuration (Debug or Release)  
    string configuration;

#if DEBUG
    configuration = "Debug";
#else
        configuration = "Release";
#endif

    return Path.Combine("..", "..", "..", "..", "MCPServer", "bin", configuration, "net8.0", "MCPServer.exe");
}

static IConfigurationRoot LoadConfiguration()
{
    // Load and validate configuration
    var config = new ConfigurationBuilder()
        .AddUserSecrets<Program>()
        .AddEnvironmentVariables()
        .Build();

    if (config["OpenAI:ApiKey"] is not { })
    {
        Console.Error.WriteLine("Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.");
        throw new InvalidOperationException("OpenAI:ApiKey is required.");
    }

    return config;
}
