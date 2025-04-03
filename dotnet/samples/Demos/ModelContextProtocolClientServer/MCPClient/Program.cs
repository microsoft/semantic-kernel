// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Transport;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

internal sealed class Program
{
    public static async Task Main(string[] args)
    {
        // Use the MCP tools with the Semantic Kernel
        await UseMCPToolsWithSKAsync();

        // Use the MCP tools and MCP prompt with the Semantic Kernel
        await UseMCPToolsAndPromptWithSKAsync();
    }

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
    private static async Task UseMCPToolsWithSKAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPToolsWithSKAsync)} sample.");

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

    /// <summary>
    /// Demonstrates how to use the MCP tools and MCP prompt with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Retrieves the list of prompts provided by the MCP server.
    /// 4. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 5. Requests the `GetCurrentWeatherForCity` prompt from the MCP server.
    /// 6. The MCP server renders the prompt using the `Boston` as value for the `city` parameter and the result of the `DateTimeUtils-GetCurrentDateTimeInUtc` server-side invocation added to the prompt as part of prompt rendering.
    /// 7. Converts the MCP server prompt: list of messages where each message is represented by content and role to a chat history.
    /// 8. Sends the chat history to the AI model together with the MCP tools represented as Kernel functions.
    /// 9. The AI model calls WeatherUtils-GetWeatherForCity function with the current date time and the `Boston` arguments extracted from the prompt to get the weather information.
    /// 10. Having received the weather information from the function call, the AI model returns the answer to the prompt.
    /// </summary>
    private static async Task UseMCPToolsAndPromptWithSKAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPToolsAndPromptWithSKAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list provided by the MCP server
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        DisplayTools(tools);

        // Retrieve and display the list of prompts provided by the MCP server
        IList<McpClientPrompt> prompts = await mcpClient.ListPromptsAsync();
        DisplayPrompts(prompts);

        // Create a kernel and register the MCP tools
        Kernel kernel = CreateKernelWithChatCompletionService();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        // Retrieve the `GetCurrentWeatherForCity` prompt from the MCP server and convert it to a chat history
        GetPromptResult promptResult = await mcpClient.GetPromptAsync("GetCurrentWeatherForCity", new Dictionary<string, object?>() { ["city"] = "Boston" });

        ChatHistory chatHistory = promptResult.ToChatHistory();

        // Execute a prompt using the MCP tools and prompt
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The weather in Boston as of 2025-04-02 16:39:40 is 61°F and rainy.
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
            const string Message = "Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.";
            Console.Error.WriteLine(Message);
            throw new InvalidOperationException(Message);
        }

        string modelId = config["OpenAI:ChatModelId"] ?? "gpt-4o-mini";

        // Create kernel
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddOpenAIChatCompletion(serviceId: "openai", modelId: modelId, apiKey: apiKey);

        return kernelBuilder.Build();
    }

    /// <summary>
    /// Creates an MCP client and connects it to the MCPServer server.
    /// </summary>
    /// <returns>An instance of <see cref="IMcpClient"/>.</returns>
    private static Task<IMcpClient> CreateMcpClientAsync()
    {
        return McpClientFactory.CreateAsync(
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
            Console.WriteLine($"- {tool.Name}: {tool.Description}");
        }
        Console.WriteLine();
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
            Console.WriteLine($"- {prompt.Name}: {prompt.Description}");
        }
        Console.WriteLine();
    }
}
