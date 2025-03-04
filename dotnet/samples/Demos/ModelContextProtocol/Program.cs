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

Kernel kernel = builder.Build();

// Add the MCP simple tools as Kernel functions
var mcpClient = await McpClientUtils.GetSimpleToolsAsync().ConfigureAwait(false);
var functions = await mcpClient.MapToFunctionsAsync().ConfigureAwait(false);

foreach (var function in functions)
{
    Console.WriteLine($"{function.Name}: {function.Description}");
}

kernel.Plugins.AddFromFunctions("GitHub", functions);

// Enable automatic function calling
var executionSettings = new OpenAIPromptExecutionSettings
{
    Temperature = 0,
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
};

// Test using GitHub tools
var result = await kernel.InvokePromptAsync("Summarize the last four commits to the microsoft/semantic-kernel repository?", new(executionSettings)).ConfigureAwait(false);
Console.WriteLine("\n\nSummary of the last four commits to the microsoft/semantic-kernel repository:");
Console.WriteLine(result);
