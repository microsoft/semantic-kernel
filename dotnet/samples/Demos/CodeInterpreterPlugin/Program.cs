// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
var modelId = configuration["OpenAI:ChatModelId"];
var endpoint = configuration["AzureContainerAppSessionPool:Endpoint"];

// Cached token for the Azure Container Apps service
string? cachedToken = null;

// Logger for program scope
ILogger logger = NullLogger.Instance;

ArgumentNullException.ThrowIfNull(apiKey);
ArgumentNullException.ThrowIfNull(modelId);
ArgumentNullException.ThrowIfNull(endpoint);

/// <summary>
/// Acquire a token for the Azure Container Apps service
/// </summary>
async Task<string> TokenProvider(CancellationToken cancellationToken)
{
    if (cachedToken is null)
    {
        string resource = "https://acasessions.io/.default";
        var credential = new InteractiveBrowserCredential();

        // Attempt to get the token
        var accessToken = await credential.GetTokenAsync(new Azure.Core.TokenRequestContext([resource]), cancellationToken).ConfigureAwait(false);
        if (logger.IsEnabled(LogLevel.Information))
        {
            logger.LogInformation("Access token obtained successfully");
        }
        cachedToken = accessToken.Token;
    }

    return cachedToken;
}

var settings = new SessionsPythonSettings(
        sessionId: Guid.NewGuid().ToString(),
        endpoint: new Uri(endpoint));

Console.WriteLine("=== Code Interpreter With Azure Container Apps Plugin Demo ===\n");

Console.WriteLine("Start your conversation with the assistant. Type enter or an empty message to quit.");

var builder =
    Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(modelId, apiKey);

// Change the log level to Trace to see more detailed logs
builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole().SetMinimumLevel(LogLevel.Information));
builder.Services.AddHttpClient();
builder.Services.AddSingleton((sp)
    => new SessionsPythonPlugin(
        settings,
        sp.GetRequiredService<IHttpClientFactory>(),
        TokenProvider,
        sp.GetRequiredService<ILoggerFactory>()));
var kernel = builder.Build();

logger = kernel.GetRequiredService<ILoggerFactory>().CreateLogger<Program>();
kernel.Plugins.AddFromObject(kernel.GetRequiredService<SessionsPythonPlugin>());
var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

var chatHistory = new ChatHistory();

StringBuilder fullAssistantContent = new();

while (true)
{
    Console.Write("\nUser: ");
    var input = Console.ReadLine();
    if (string.IsNullOrWhiteSpace(input)) { break; }

    chatHistory.AddUserMessage(input);

    Console.WriteLine("Assistant: ");
    fullAssistantContent.Clear();
    await foreach (var content in chatCompletion.GetStreamingChatMessageContentsAsync(
        chatHistory,
        new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() },
        kernel)
        .ConfigureAwait(false))
    {
        Console.Write(content.Content);
        fullAssistantContent.Append(content.Content);
    }
    chatHistory.AddAssistantMessage(fullAssistantContent.ToString());
}
