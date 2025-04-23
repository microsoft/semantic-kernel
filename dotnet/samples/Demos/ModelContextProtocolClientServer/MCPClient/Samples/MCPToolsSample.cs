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
/// This sample demonstrates how to use the Model Context Protocol (MCP) tools with the Semantic Kernel.
/// </summary>
internal sealed class MCPToolsSample : BaseSample
{
    /// <summary>
    /// Demonstrates how to use the MCP tools with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 4. Sends the prompt to AI model together with the MCP tools represented as Kernel functions.
    /// 5. The AI model calls DateTimeUtils-GetCurrentDateTimeInUtc function to get the current date time in UTC required as an argument for the next function.
    /// 6. The AI model calls WeatherUtils-GetWeatherForCity function with the current date time and the `Boston` arguments extracted from the prompt to get the weather information.
    /// 7. Having received the weather information from the function call, the AI model returns the answer to the prompt.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(MCPToolsSample)} sample.");

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
        Console.WriteLine(prompt);

        // Execute a prompt using the MCP tools. The AI model will automatically call the appropriate MCP tools to answer the prompt.
        FunctionResult result = await kernel.InvokePromptAsync(prompt, new(executionSettings));

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The likely color of the sky in Boston today is gray, as it is currently rainy.
    }
}
