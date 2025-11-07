// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates how to use an Agent with function tools provided via an OpenAPI spec with both Semantic Kernel and Agent Framework.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o-mini";

await SKAgent();
await AFAgent();

async Task SKAgent()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    // Create an OpenAI chat client kernel.
    var kernel = Kernel.CreateBuilder().AddAzureOpenAIChatClient(deploymentName, endpoint, new AzureCliCredential()).Build();

    // Load the OpenAPI Spec from a file.
    var plugin = await kernel.ImportPluginFromOpenApiAsync("github", "OpenAPISpec.json");

    // Create the agent, and provide the kernel with the OpenAPI function tools to the agent.
    var agent = new ChatCompletionAgent()
    {
        Kernel = kernel,
        Instructions = "You are a helpful assistant",
        Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };

    // Run the agent with the OpenAPI function tools.
    await foreach (var result in agent.InvokeAsync("Please list the names, colors and descriptions of all the labels available in the microsoft/agent-framework repository on github."))
    {
        Console.WriteLine(result.Message);
    }
}

async Task AFAgent()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    // Load the OpenAPI Spec from a file.
    KernelPlugin plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("github", "OpenAPISpec.json");

    // Convert the Semantic Kernel plugin to Agent Framework function tools.
    // This requires a dummy Kernel instance, since KernelFunctions cannot execute without one.
    Kernel kernel = new();
    List<AITool> tools = plugin.Select(x => x.WithKernel(kernel)).Cast<AITool>().ToList();

    // Create the chat client and agent, and provide the OpenAPI function tools to the agent.
    AIAgent agent = new AzureOpenAIClient(
        new Uri(endpoint),
        new AzureCliCredential())
        .GetChatClient(deploymentName)
        .CreateAIAgent(instructions: "You are a helpful assistant", tools: tools);

    // Run the agent with the OpenAPI function tools.
    Console.WriteLine(await agent.RunAsync("Please list the names, colors and descriptions of all the labels available in the microsoft/agent-framework repository on github."));
}
