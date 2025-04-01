// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Transport;

namespace MCPClient;

internal sealed class Program
{
    public static async Task Main(string[] args)
    {
        // Load and validate configuration
        var config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        if (config["OpenAI:ApiKey"] is not { } apiKey)
        {
            Console.Error.WriteLine("Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.");
            return;
        }

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
        var tools = await mcpClient.ListToolsAsync().ConfigureAwait(false);
        foreach (var tool in tools)
        {
            Console.WriteLine($"{tool.Name}: {tool.Description}");
        }

        // Prepare and build kernel with the MCP tools as Kernel functions
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));
        kernelBuilder.Services
            .AddLogging(c => c.AddDebug().SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Trace))
            .AddOpenAIChatCompletion(serviceId: "openai", modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o-mini", apiKey: apiKey);

        Kernel kernel = kernelBuilder.Build();

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        // Execute a prompt using the MCP tools. The AI model will automatically call the appropriate MCP tools to answer the prompt.
        var prompt = "What is the likely color of the sky in Boston today?";
        var result = await kernel.InvokePromptAsync(prompt, new(executionSettings)).ConfigureAwait(false);
        Console.WriteLine($"\n\n{prompt}\n{result}");

        // The expected output is:
        // What is the likely color of the sky in Boston today?
        // The likely color of the sky in Boston today is gray, as it is currently rainy.
    }

    /// <summary>
    /// Returns the path to the MCPServer server executable.
    /// </summary>
    /// <returns>The path to the MCPServer server executable.</returns>
    private static string GetMCPServerPath()
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
}
