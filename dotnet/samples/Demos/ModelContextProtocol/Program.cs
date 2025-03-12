// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol;

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

// Prepare and build kernel
var builder = Kernel.CreateBuilder();
builder.Services.AddLogging(c => c.AddDebug().SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Trace));

if (config["OpenAI:ApiKey"] is not null)
{
    builder.Services.AddOpenAIChatCompletion(
        serviceId: "openai",
        modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o",
        apiKey: config["OpenAI:ApiKey"]!);
}
else
{
    Console.Error.WriteLine("Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.");
    return;
}

Kernel kernel = builder.Build();

// Create an MCPClient for the GitHub server
var mcpClient = await McpDotNetExtensions.GetGitHubToolsAsync().ConfigureAwait(false);

// Retrieve the list of tools available on the GitHub server
var tools = await mcpClient.ListToolsAsync().ConfigureAwait(false);
foreach (var tool in tools.Tools)
{
    Console.WriteLine($"{tool.Name}: {tool.Description}");
}

// Add the MCP tools as Kernel functions
var functions = await mcpClient.MapToFunctionsAsync().ConfigureAwait(false);
kernel.Plugins.AddFromFunctions("GitHub", functions);

// Enable automatic function calling
var executionSettings = new OpenAIPromptExecutionSettings
{
    Temperature = 0,
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
};

// Test using GitHub tools
var prompt = "Summarize the last four commits to the microsoft/semantic-kernel repository?";
var result = await kernel.InvokePromptAsync(prompt, new(executionSettings)).ConfigureAwait(false);
Console.WriteLine($"\n\n{prompt}\n{result}");
