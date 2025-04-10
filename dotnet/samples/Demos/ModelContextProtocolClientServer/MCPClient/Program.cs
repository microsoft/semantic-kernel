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
        await UseMCPToolsAsync();

        await UseMCPPromptAsync();

        await UseMCPResourcesAsync();

        await UseMCPResourceTemplatesAsync();
    }

    /// <summary>
    /// Demonstrates how to use the MCP resources with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of resources provided by the MCP server.
    /// 3. Retrieves the `image://cat.jpg` resource content from the MCP server.
    /// 4. Adds the image to the chat history and prompts the AI model to describe the content of the image.
    /// </summary>
    private static async Task UseMCPResourcesAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPResourcesAsync)} sample.");

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
    /// Demonstrates how to use the MCP resource templates with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of resource templates provided by the MCP server.
    /// 3. Reads relevant to the prompt records from the `vectorStore://records/{prompt}` MCP resource template.
    /// 4. Adds the records to the chat history and prompts the AI model to explain what SK is.
    /// </summary>
    private static async Task UseMCPResourceTemplatesAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPResourceTemplatesAsync)} sample.");

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
    private static async Task UseMCPToolsAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPToolsAsync)} sample.");

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
    /// Demonstrates how to use the MCP prompt with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of prompts provided by the MCP server.
    /// 3. Gets the current weather for Boston and Sydney using the `GetCurrentWeatherForCity` prompt.
    /// 4. Adds the MCP server prompts to the chat history and prompts the AI model to compare the weather in the two cities and suggest the best place to go for a walk.
    /// 5. After receiving and processing the weather data for both cities and the prompt, the AI model returns an answer.
    /// </summary>
    private static async Task UseMCPPromptAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPPromptAsync)} sample.");

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
            Console.WriteLine($"- Name: {tool.Name}, Description: {tool.Description}");
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
            Console.WriteLine($"- Name: {prompt.Name}, Description: {prompt.Description}");
        }
        Console.WriteLine();
    }

    private static void DisplayResources(IList<Resource> resources)
    {
        Console.WriteLine("Available MCP resources:");
        foreach (var resource in resources)
        {
            Console.WriteLine($"- Name: {resource.Name}, Uri: {resource.Uri}, Description: {resource.Description}");
        }
        Console.WriteLine();
    }

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
