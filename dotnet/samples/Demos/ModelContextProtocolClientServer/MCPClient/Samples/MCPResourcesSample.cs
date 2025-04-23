// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient.Samples;

/// <summary>
/// Demonstrates how to use the Model Context Protocol (MCP) resources with the Semantic Kernel.
/// </summary>
internal sealed class MCPResourcesSample : BaseSample
{
    /// <summary>
    /// Demonstrates how to use the MCP resources with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of resources provided by the MCP server.
    /// 3. Retrieves the `image://cat.jpg` resource content from the MCP server.
    /// 4. Adds the image to the chat history and prompts the AI model to describe the content of the image.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(MCPResourcesSample)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve list of resources provided by the MCP server and display them
        IList<Resource> resources = await mcpClient.ListResourcesAsync();
        DisplayResources(resources);

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        // Retrieve the `image://cat.jpg` resource from the MCP server
        ReadResourceResult resource = await mcpClient.ReadResourceAsync("image://cat.jpg");

        // Add the resource to the chat history and prompt the AI model to describe the content of the image
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage(resource.ToChatMessageContentItemCollection());
        chatHistory.AddUserMessage("Describe the content of the image?");

        // Execute a prompt using the MCP resource and prompt added to the chat history
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The image features a fluffy cat sitting in a lush, colorful garden.
        // The garden is filled with various flowers and plants, creating a vibrant and serene atmosphere...
    }

    /// <summary>
    /// Displays the list of resources provided by the MCP server.
    /// </summary>
    /// <param name="resources">The list of resources to display.</param>
    private static void DisplayResources(IList<Resource> resources)
    {
        Console.WriteLine("Available MCP resources:");
        foreach (var resource in resources)
        {
            Console.WriteLine($"- Name: {resource.Name}, Uri: {resource.Uri}, Description: {resource.Description}");
        }
        Console.WriteLine();
    }
}
