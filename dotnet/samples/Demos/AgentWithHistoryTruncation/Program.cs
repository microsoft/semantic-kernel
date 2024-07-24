// Copyright (c) Microsoft. All rights reserved.

using AgentWithHistoryTruncation;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build()
    .Get<AppConfig>() ??
    throw new InvalidOperationException("Configuration is not setup correctly.");

config.Validate();

// Prepare and build kernel
IKernelBuilder builder = Kernel.CreateBuilder();

builder.Services.AddLogging(c => c.AddDebug().SetMinimumLevel(LogLevel.Trace));

// Adding chat completion service
if (config.IsAzureOpenAIConfigured)
{
    // Use Azure OpenAI Deployments
    builder.Services.AddAzureOpenAIChatCompletion(
        config.AzureOpenAI!.ChatDeploymentName!,
        config.AzureOpenAI.Endpoint!,
        config.AzureOpenAI.ApiKey!);
}
else
{
    // Use OpenAI
    builder.Services.AddOpenAIChatCompletion(
        config.OpenAI!.ModelId!,
        config.OpenAI.ApiKey!,
        config.OpenAI.OrgId);
}

Kernel kernel = builder.Build();

TruncatingChatAgent agent =
    new()
    {
        Kernel = kernel,
        TruncationStrategy = new MessageCountTruncationStrategy(3) // AI sees only the last 3 messages: User , Assistant, User
    };

AgentGroupChat chat = new();

// Start the conversation
string? input = null;

while (true)
{
    Console.Write("User > ");
    input = Console.ReadLine();

    if (string.IsNullOrWhiteSpace(input))
    {
        // Leaves if the user hit enter without typing any word
        break;
    }

    chat.AddChatMessage(new(AuthorRole.User, input));

    // Get the result from the AI
    await foreach (ChatMessageContent message in chat.InvokeAsync(agent))
    {
        // Print the result
        Console.WriteLine("Assistant > " + message.Content);
    }
}
