// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using RepoUtils;

#pragma warning disable RCS1110 // Declare type inside namespace.
#pragma warning disable CA1819 // Properties should not return arrays

/**
 * This example shows how to use multiple prompt template formats.
 */
// ReSharper disable once InconsistentNaming
public static class Example72_KernelStreaming
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync()
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        Kernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .Build();

        var funyParagraphFunction = kernel.CreateFunctionFromPrompt("Write a funny paragraph about streaming", new OpenAIRequestSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        var roleDisplayed = false;

        Console.WriteLine("\n===  Semantic Function - Streaming ===\n");

        // Streaming can be of any type depending on the underlying service the function is using.
        await foreach (var update in kernel.RunStreamingAsync<StreamingChatContent>(funyParagraphFunction))
        {
            // You will be always able to know the type of the update by checking the Type property.
            if (!roleDisplayed && update.Role.HasValue)
            {
                Console.WriteLine($"Role: {update.Role}");
                roleDisplayed = true;
            }

            if (update.Content is { Length: > 0 })
            {
                Console.Write(update.Content);
            }
        };
    }
}
