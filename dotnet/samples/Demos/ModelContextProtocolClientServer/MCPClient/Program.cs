// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
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
        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list provided by the MCP server
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        DisplayTools(tools);

        // Create a kernel and register the MCP tools
        Kernel kernel = CreateKernelWithChatCompletionService();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        string prompt = "What is the likely color of the sky in Boston today?";

        // Execute a prompt using the MCP tools. The AI model will automatically call the appropriate MCP tools to answer the prompt.
        FunctionResult result = await kernel.InvokePromptAsync(prompt, new(executionSettings)).ConfigureAwait(false);

        Console.WriteLine(result);

        // The expected output is: The likely color of the sky in Boston today is gray, as it is currently rainy.
    }

    /// <summary>
    /// Creates an instance of <see cref="Kernel"/> with the OpenAI chat completion service registered.
    /// </summary>
    /// <returns>An instance of <see cref="Kernel"/>.</returns>
    private static Kernel CreateKernelWithChatCompletionService()
    {
        // Load and validate configuration
        IConfigurationRoot config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        if (config["OpenAI:ApiKey"] is not { } apiKey)
        {
            string message = "Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.";
            Console.Error.WriteLine(message);
            throw new InvalidOperationException(message);
        }

        // Create kernel
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddOpenAIChatCompletion(serviceId: "openai", modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o-mini", apiKey: config["OpenAI:ApiKey"]!);

        return kernelBuilder.Build();
    }

    /// <summary>
    /// Creates an MCP client and connects it to the MCPServer server.
    /// </summary>
    /// <returns>An instance of <see cref="IMcpClient"/>.</returns>
    private static async Task<IMcpClient> CreateMcpClientAsync()
    {
        var mcpClient = await McpClientFactory.CreateAsync(
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

        return mcpClient;
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

    /// <summary>
    /// Displays the list of available MCP tools.
    /// </summary>
    /// <param name="tools">The list of the tools to display.</param>
    private static void DisplayTools(IList<McpClientTool> tools)
    {
        Console.WriteLine("Available MCP tools:");
        foreach (var tool in tools)
        {
            Console.WriteLine($"{tool.Name}: {tool.Description}");
        }
    }
}
