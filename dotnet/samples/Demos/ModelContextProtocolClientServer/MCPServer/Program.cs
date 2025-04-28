// Copyright (c) Microsoft. All rights reserved.

using MCPServer;
using MCPServer.Tools;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

var builder = Host.CreateEmptyApplicationBuilder(settings: null);

// Load and validate configuration
(string embeddingModelId, string chatModelId, string apiKey) = GetConfiguration();

await builder.Build().RunAsync();

/// <summary>
/// Creates a sales assistant agent that can place orders and handle refunds.
/// </summary>
/// <remarks>
/// The agent is created with an OpenAI chat completion service and a plugin for order processing.
/// </remarks>
static Agent CreateSalesAssistantAgent(string chatModelId, string apiKey)
{
    IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

    // Register the SK plugin for the agent to use
    kernelBuilder.Plugins.AddFromType<OrderProcessingUtils>();

    // Register chat completion service
    kernelBuilder.Services.AddOpenAIChatCompletion(chatModelId, apiKey);

    // Using a dedicated kernel with the `OrderProcessingUtils` plugin instead of the global kernel has a few advantages:
    // - The agent has access to only relevant plugins, leading to better decision-making regarding which plugin to use.
    //   Fewer plugins mean less ambiguity in selecting the most appropriate one for a given task.
    // - The plugin is isolated from other plugins exposed by the MCP server. As a result the client's Agent/AI model does
    //   not have access to irrelevant plugins.
    Kernel kernel = kernelBuilder.Build();

    // Define the agent
    return new ChatCompletionAgent()
    {
        Name = "SalesAssistant",
        Instructions = "You are a sales assistant. Place orders for items the user requests and handle refunds.",
        Description = "Agent to invoke to place orders for items the user requests and handle refunds.",
        Kernel = kernel,
        Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };
}

/// <summary>
/// Gets configuration.
/// </summary>
static (string EmbeddingModelId, string ChatModelId, string ApiKey) GetConfiguration()
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

    string embeddingModelId = config["OpenAI:EmbeddingModelId"] ?? "text-embedding-3-small";

    string chatModelId = config["OpenAI:ChatModelId"] ?? "gpt-4o-mini";

    return (embeddingModelId, chatModelId, apiKey);
}
