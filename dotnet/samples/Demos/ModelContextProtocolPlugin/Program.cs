// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Types;

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

if (config["OpenAI:ApiKey"] is not { } apiKey)
{
    Console.Error.WriteLine("Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.");
    return;
}

// Create an MCPClient for the GitHub server
await using var mcpClient = await McpClientFactory.CreateAsync(
    new McpServerConfig()
    {
        Id = "github",
        Name = "GitHub",
        TransportType = "stdio",
        TransportOptions = new Dictionary<string, string>
        {
            ["command"] = "npx",
            ["arguments"] = "-y @modelcontextprotocol/server-github",
        }
    },
    new McpClientOptions()
    {
        ClientInfo = new Implementation()
        {
            Name = "GitHub",
            Version = "1.0.0"
        }
    }).ConfigureAwait(false);

// Retrieve the list of tools available on the GitHub server
var tools = await mcpClient.ListToolsAsync().ConfigureAwait(false);
foreach (var tool in tools)
{
    Console.WriteLine($"{tool.Name}: {tool.Description}");
}

// Prepare and build kernel with the MCP tools as Kernel functions
var builder = Kernel.CreateBuilder();
builder.Services
    .AddLogging(c => c.AddDebug().SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Trace))
    .AddOpenAIChatCompletion(
        modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o-mini",
        apiKey: apiKey);
Kernel kernel = builder.Build();
kernel.Plugins.AddFromFunctions("GitHub", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

// Enable automatic function calling
OpenAIPromptExecutionSettings executionSettings = new()
{
    Temperature = 0,
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
};

// Test using GitHub tools
var prompt = "Summarize the last four commits to the microsoft/semantic-kernel repository?";
var result = await kernel.InvokePromptAsync(prompt, new(executionSettings)).ConfigureAwait(false);
Console.WriteLine($"\n\n{prompt}\n{result}");
