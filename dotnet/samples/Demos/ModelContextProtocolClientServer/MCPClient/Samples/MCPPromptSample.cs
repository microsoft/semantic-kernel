// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient.Samples;

/// <summary>
/// Demonstrates how to use the Model Context Protocol (MCP) prompt with the Semantic Kernel.
/// </summary>
internal sealed class MCPPromptSample : BaseSample
{
    /// <summary>
    /// Demonstrates how to use the MCP prompt with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of prompts provided by the MCP server.
    /// 3. Gets the current weather for Boston and Sydney using the `GetCurrentWeatherForCity` prompt.
    /// 4. Adds the MCP server prompts to the chat history and prompts the AI model to compare the weather in the two cities and suggest the best place to go for a walk.
    /// 5. After receiving and processing the weather data for both cities and the prompt, the AI model returns an answer.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(MCPPromptSample)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list of prompts provided by the MCP server
        IList<McpClientPrompt> prompts = await mcpClient.ListPromptsAsync();
        DisplayPrompts(prompts);

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Get weather for Boston using the `GetCurrentWeatherForCity` prompt from the MCP server
        GetPromptResult bostonWeatherPrompt = await mcpClient.GetPromptAsync("GetCurrentWeatherForCity", new Dictionary<string, object?>() { ["city"] = "Boston", ["time"] = DateTime.UtcNow.ToString() });

        // Get weather for Sydney using the `GetCurrentWeatherForCity` prompt from the MCP server
        GetPromptResult sydneyWeatherPrompt = await mcpClient.GetPromptAsync("GetCurrentWeatherForCity", new Dictionary<string, object?>() { ["city"] = "Sydney", ["time"] = DateTime.UtcNow.ToString() });

        // Add the prompts to the chat history
        ChatHistory chatHistory = [];
        chatHistory.AddRange(bostonWeatherPrompt.ToChatMessageContents());
        chatHistory.AddRange(sydneyWeatherPrompt.ToChatMessageContents());
        chatHistory.AddUserMessage("Compare the weather in the two cities and suggest the best place to go for a walk.");

        // Execute a prompt using the MCP tools and prompt
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, kernel: kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: Given these conditions, Sydney would be the better choice for a pleasant walk, as the sunny and warm weather is ideal for outdoor activities.
        // The rain in Boston could make walking less enjoyable and potentially inconvenient.
    }

    /// <summary>
    /// Displays the list of available MCP prompts.
    /// </summary>
    /// <param name="prompts">The list of the prompts to display.</param>
    private static void DisplayPrompts(IList<McpClientPrompt> prompts)
    {
        Console.WriteLine("Available MCP prompts:");
        foreach (var prompt in prompts)
        {
            Console.WriteLine($"- Name: {prompt.Name}, Description: {prompt.Description}");
        }
        Console.WriteLine();
    }
}
