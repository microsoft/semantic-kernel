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
/// Demonstrates how to use the Model Context Protocol (MCP) resource templates with the Semantic Kernel.
/// </summary>
internal sealed class MCPResourceTemplatesSample : BaseSample
{
    /// <summary>
    /// Demonstrates how to use the MCP resource templates with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of resource templates provided by the MCP server.
    /// 3. Reads relevant to the prompt records from the `vectorStore://records/{prompt}` MCP resource template.
    /// 4. Adds the records to the chat history and prompts the AI model to explain what SK is.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(MCPResourceTemplatesSample)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve list of resource templates provided by the MCP server and display them
        IList<ResourceTemplate> resourceTemplates = await mcpClient.ListResourceTemplatesAsync();
        DisplayResourceTemplates(resourceTemplates);

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        string prompt = "What is the Semantic Kernel?";

        // Retrieve relevant to the prompt records via MCP resource template
        ReadResourceResult resource = await mcpClient.ReadResourceAsync($"vectorStore://records/{prompt}");

        // Add the resource content/records to the chat history and prompt the AI model to explain what SK is
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage(resource.ToChatMessageContentItemCollection());
        chatHistory.AddUserMessage(prompt);

        // Execute a prompt using the MCP resource and prompt added to the chat history
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The Semantic Kernel (SK) is a lightweight software development kit (SDK) designed for use in .NET applications.
        // It acts as an orchestrator that facilitates interaction between AI models and available plugins, enabling them to work together to produce desired outputs.
    }

    /// <summary>
    /// Displays the list of resource templates provided by the MCP server.
    /// </summary>
    /// <param name="resourceTemplates">The list of resource templates to display.</param>
    private static void DisplayResourceTemplates(IList<ResourceTemplate> resourceTemplates)
    {
        Console.WriteLine("Available MCP resource templates:");
        foreach (var template in resourceTemplates)
        {
            Console.WriteLine($"- Name: {template.Name}, Description: {template.Description}");
        }
        Console.WriteLine();
    }
}
