// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Plugins;

// Use this for application permissions
string[] scopes;

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build()
    .Get<AppConfig>() ??
    throw new InvalidOperationException("Configuration is not setup correctly.");

config.Validate();

TokenCredential credential = null!;
if (config.AzureEntraId!.InteractiveBrowserAuthentication) // Authentication As User
{
    /// Use this if using user delegated permissions
    scopes = ["User.Read", "BookingsAppointment.ReadWrite.All"];

    credential = new InteractiveBrowserCredential(
        new InteractiveBrowserCredentialOptions
        {
            TenantId = config.AzureEntraId.TenantId,
            ClientId = config.AzureEntraId.ClientId,
            AuthorityHost = AzureAuthorityHosts.AzurePublicCloud,
            RedirectUri = new Uri(config.AzureEntraId.InteractiveBrowserRedirectUri!)
        });
}
else // Authentication As Application
{
    scopes = ["https://graph.microsoft.com/.default"];

    credential = new ClientSecretCredential(
        config.AzureEntraId.TenantId,
        config.AzureEntraId.ClientId,
        config.AzureEntraId.ClientSecret);
}

var graphClient = new GraphServiceClient(credential, scopes);

// Prepare and build kernel
var builder = Kernel.CreateBuilder();

builder.Services.AddLogging(c => c.AddDebug().SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Trace));

builder.Plugins.AddFromObject(new BookingsPlugin(
    graphClient,
    config.BookingBusinessId!,
    config.BookingServiceId!));

// Adding chat completion service
if (config.IsAzureOpenAIConfigured)
{
    // Use Azure OpenAI Deployments
    builder.Services.AddAzureOpenAIChatCompletion(
        config.AzureOpenAI!.DeploymentName!,
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

// Create chat history
ChatHistory chatHistory = [];

// Get chat completion service
var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

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

    // Add the message from the user to the chat history
    chatHistory.AddUserMessage(input);

    // Enable auto function calling
    var executionSettings = new OpenAIPromptExecutionSettings
    {
        ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
    };

    // Get the result from the AI
    var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

    // Print the result
    Console.WriteLine("Assistant > " + result);

    // Add the message from the agent to the chat history
    chatHistory.AddMessage(result.Role, result?.Content!);
}
