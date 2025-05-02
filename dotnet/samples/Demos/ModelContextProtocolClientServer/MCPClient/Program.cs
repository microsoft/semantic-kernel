// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Transport;

namespace MCPClient;

internal sealed class Program
{
    /// <summary>
    /// Main method to run all the samples.
    /// </summary>
    public static async Task Main(string[] args)
    {
        // Load and validate configuration
        (string deploymentName, string endPoint, string apiKey) = GetConfiguration();


    }

    /// <summary>
    /// Creates an MCP client and connects it to the MCPServer server.
    /// </summary>
    /// <returns>An instance of <see cref="IMcpClient"/>.</returns>
    private static Task<IMcpClient> CreateMcpClientAsync()
    {
        // Create and return the MCP client
        return McpClientFactory.CreateAsync(
            clientTransport: new StdioClientTransport(new StdioClientTransportOptions
            {
                Name = "MCPServer",
                Command = Path.Combine("..", "..", "..", "..", "MCPServer", "bin", "Debug", "net8.0", "MCPServer.exe"), // Path to the MCPServer executable
            })
         );
    }

    /// <summary>
    /// Gets configuration.
    /// </summary>
    private static (string DeploymentName, string Endpoint, string ApiKey) GetConfiguration()
    {
        // Load and validate configuration
        IConfigurationRoot config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        if (config["AzureOpenAI:Endpoint"] is not { } endpoint)
        {
            const string Message = "Please provide a valid AzureOpenAI:Endpoint to run this sample.";
            Console.Error.WriteLine(Message);
            throw new InvalidOperationException(Message);
        }

        if (config["AzureOpenAI:ApiKey"] is not { } apiKey)
        {
            const string Message = "Please provide a valid AzureOpenAI:ApiKey to run this sample.";
            Console.Error.WriteLine(Message);
            throw new InvalidOperationException(Message);
        }

        string deploymentName = config["AzureOpenAI:ChatDeploymentName"] ?? "gpt-4o-mini";

        return (deploymentName, endpoint, apiKey);
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
            Console.WriteLine($"- Name: {tool.Name}, Description: {tool.Description}");
        }
        Console.WriteLine();
    }
}
