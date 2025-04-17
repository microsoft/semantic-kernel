// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using ModelContextProtocol.Client;

namespace MCPClient.Samples;

/// <summary>
/// Demonstrates how to use <see cref="AzureAIAgent"/> with MCP tools represented as Kernel functions.
/// </summary>
internal sealed class AzureAIAgentWithMCPToolsSample : BaseSample
{
    /// <summary>
    /// Demonstrates how to use <see cref="AzureAIAgent"/> with MCP tools represented as Kernel functions.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 4. Defines Azure AI agent with instructions, name, kernel, and arguments.
    /// 5. Invokes the agent with a prompt.
    /// 6. The agent sends the prompt to the AI model, together with the MCP tools represented as Kernel functions.
    /// 7. The AI model calls DateTimeUtils-GetCurrentDateTimeInUtc function to get the current date time in UTC required as an argument for the next function.
    /// 8. The AI model calls WeatherUtils-GetWeatherForCity function with the current date time and the `Boston` arguments extracted from the prompt to get the weather information.
    /// 9. Having received the weather information from the function call, the AI model returns the answer to the agent and the agent returns the answer to the user.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(AzureAIAgentWithMCPToolsSample)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list provided by the MCP server
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        DisplayTools(tools);

        // Create a kernel and register the MCP tools as Kernel functions
        Kernel kernel = new();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Define the agent using the kernel with registered MCP tools
        AzureAIAgent agent = await CreateAzureAIAgentAsync(
            name: "WeatherAgent",
            instructions: "Answer questions about the weather.",
            kernel: kernel
        );

        // Invokes agent with a prompt
        string prompt = "What is the likely color of the sky in Boston today?";
        Console.WriteLine(prompt);

        AgentResponseItem<ChatMessageContent> response = await agent.InvokeAsync(message: prompt).FirstAsync();
        Console.WriteLine(response.Message);
        Console.WriteLine();

        // The expected output is: Today in Boston, the weather is 61°F and rainy. Due to the rain, the likely color of the sky will be gray.

        // Delete the agent thread after use
        await response!.Thread.DeleteAsync();

        // Delete the agent after use
        await agent.Client.DeleteAgentAsync(agent.Id);
    }

    /// <summary>
    /// Creates an instance of <see cref="AzureAIAgent"/> with the specified name and instructions.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="name">The name of the agent.</param>
    /// <param name="instructions">The instructions for the agent.</param>
    /// <returns>An instance of <see cref="AzureAIAgent"/>.</returns>
    private static async Task<AzureAIAgent> CreateAzureAIAgentAsync(Kernel kernel, string name, string instructions)
    {
        // Load and validate configuration
        IConfigurationRoot config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        if (config["AzureAI:ConnectionString"] is not { } connectionString)
        {
            const string Message = "Please provide a valid `AzureAI:ConnectionString` secret to run this sample. See the associated README.md for more details.";
            Console.Error.WriteLine(Message);
            throw new InvalidOperationException(Message);
        }

        string modelId = config["AzureAI:ChatModelId"] ?? "gpt-4o-mini";

        // Create the Azure AI Agent
        AIProjectClient projectClient = AzureAIAgent.CreateAzureAIClient(connectionString, new AzureCliCredential());

        AgentsClient agentsClient = projectClient.GetAgentsClient();

        Azure.AI.Projects.Agent agent = await agentsClient.CreateAgentAsync(modelId, name, null, instructions);

        return new AzureAIAgent(agent, agentsClient)
        {
            Kernel = kernel
        };
    }
}
