// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

#pragma warning disable RCS1110 // Declare type inside namespace.
#pragma warning disable CA1819 // Properties should not return arrays

/**
 * This example shows how to use multiple prompt template formats.
 */
// ReSharper disable once InconsistentNaming
public static class Example67_KernelStreaming
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync()
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, deploymentName or modelId not found. Skipping example.");
            return;
        }

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey,
                modelId: chatModelId)
            .Build();

        var funnyParagraphFunction = kernel.CreateFunctionFromPrompt("Write a funny paragraph about streaming", new OpenAIPromptExecutionSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        var roleDisplayed = false;

        Console.WriteLine("\n===  Prompt Function - Streaming ===\n");

        // Streaming can be of any type depending on the underlying service the function is using.
        await foreach (var update in kernel.InvokeStreamingAsync<OpenAIStreamingChatMessageContent>(funnyParagraphFunction))
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
        }
    }
}
