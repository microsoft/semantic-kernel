// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

#pragma warning disable SKEXP0050 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var configuration = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

var apiKey = configuration["OpenAI:ApiKey"];
var token = configuration["AzureContainerApps:BearerKey"];
var endpoint = configuration["AzureContainerApps:Endpoint"];

ArgumentNullException.ThrowIfNull(apiKey);
ArgumentNullException.ThrowIfNull(token);
ArgumentNullException.ThrowIfNull(endpoint);

Task<string> TokenProvider() => Task.FromResult(token);

var settings = new SessionPythonSettings()
{
    Endpoint = new Uri(endpoint),
    SessionId = Guid.NewGuid().ToString()
};

Console.WriteLine("=== Code Interpreter With Azure Container Apps Plugin Demo ===");

var builder =
    Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("gpt-3.5-turbo", apiKey);

builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole());
builder.Services.AddHttpClient();
builder.Services.AddSingleton((sp)
    => new SessionsPythonPlugin(
        settings,
        TokenProvider,
        sp.GetRequiredService<IHttpClientFactory>(),
        sp.GetRequiredService<ILoggerFactory>()));
var kernel = builder.Build();

kernel.Plugins.AddFromObject(kernel.GetRequiredService<SessionsPythonPlugin>());
var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

var chatHistory = new ChatHistory();

StringBuilder fullAssistantContent = new();

do
{
    Console.Write("\nUser: ");
    var input = Console.ReadLine();
    if (string.IsNullOrWhiteSpace(input)) { break; }

    chatHistory.AddUserMessage(input);

    Console.WriteLine("Assistant: ");
    fullAssistantContent.Clear();
    await foreach (var content in chatCompletion.GetStreamingChatMessageContentsAsync(
        chatHistory,
        new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
        kernel)
        .ConfigureAwait(false))
    {
        Console.Write(content.Content);
        fullAssistantContent.Append(content.Content);
    }
    chatHistory.AddAssistantMessage(fullAssistantContent.ToString());
} while (true);
