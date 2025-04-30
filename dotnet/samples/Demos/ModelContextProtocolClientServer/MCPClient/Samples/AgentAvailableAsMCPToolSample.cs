// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol.Client;

namespace MCPClient.Samples;

/// <summary>
/// Demonstrates how to use SK agent available as MCP tool.
/// </summary>
internal sealed class AgentAvailableAsMCPToolSample : BaseSample
{
    /// <summary>
    /// Demonstrates how to use SK agent available as MCP tool.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 4. Sends the prompt to AI model together with the MCP tools represented as Kernel functions.
    /// 5. The AI model calls the `Agents_SalesAssistant` function, which calls the MCP tool that calls the SK agent on the server.
    /// 6. The agent calls the `OrderProcessingUtils-PlaceOrder` function to place the order for the `Grande Mug`.
    /// 7. The agent calls the `OrderProcessingUtils-ReturnOrder` function to return the `Wide Rim Mug`.
    /// 8. The agent summarizes the transactions and returns the result as part of the `Agents_SalesAssistant` function call.
    /// 9. Having received the result from the `Agents_SalesAssistant`, the AI model returns the answer to the prompt.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(AgentAvailableAsMCPToolSample)} sample.");

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

        string prompt = "I'd like to order the 'Grande Mug' and return the 'Wide Rim Mug' bought last week.";
        Console.WriteLine(prompt);

        // Execute a prompt using the MCP tools. The AI model will automatically call the appropriate MCP tools to answer the prompt.
        FunctionResult result = await kernel.InvokePromptAsync(prompt, new(executionSettings));

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The order for the "Grande Mug" has been successfully placed.
        // Additionally, the return process for the "Wide Rim Mug" has been successfully initiated.
        // If you have any further questions or need assistance with anything else, feel free to ask!
    }
}
