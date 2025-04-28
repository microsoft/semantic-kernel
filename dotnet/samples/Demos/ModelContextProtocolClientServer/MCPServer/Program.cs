// Copyright (c) Microsoft. All rights reserved.

using MCPServer;
using MCPServer.Tools;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

var builder = Host.CreateEmptyApplicationBuilder(settings: null);



await builder.Build().RunAsync();

/// <summary>
/// Creates a sales assistant agent that can place orders and handle refunds.
/// </summary>
/// <remarks>
/// The agent is created with an OpenAI chat completion service and a plugin for order processing.
/// </remarks>
static Agent CreateSalesAssistantAgent()
{
    // Load and validate configuration
    (string deploymentName, string endPoint, string apiKey) = GetConfiguration();

    IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

    // Register the SK plugin for the agent to use
    kernelBuilder.Plugins.AddFromType<OrderProcessingUtils>();

    // Register chat completion service
    kernelBuilder.Services.AddAzureOpenAIChatCompletion(deploymentName: deploymentName, endpoint: endPoint, apiKey: apiKey);

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
static (string DeploymentName, string Endpoint, string ApiKey) GetConfiguration()
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
