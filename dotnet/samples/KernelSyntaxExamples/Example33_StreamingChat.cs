// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/**
 * The following example shows how to use Semantic Kernel with streaming Chat Completion
 */
// ReSharper disable once InconsistentNaming
public static class Example33_StreamingChat
{
    public static async Task RunAsync()
    {
        await AzureOpenAIChatStreamSampleAsync();
        await OpenAIChatStreamSampleAsync();
    }

    private static async Task OpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Open AI - ChatGPT Streaming ========");

        OpenAIChatCompletion openAIChatCompletion = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        await StartStreamingChatAsync(openAIChatCompletion);
    }

    private static async Task AzureOpenAIChatStreamSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI - ChatGPT Streaming ========");

        AzureOpenAIChatCompletion azureOpenAIChatCompletion = new(
           TestConfiguration.AzureOpenAI.ChatDeploymentName,
           TestConfiguration.AzureOpenAI.Endpoint,
           TestConfiguration.AzureOpenAI.ApiKey);

        await StartStreamingChatAsync(azureOpenAIChatCompletion);
    }

    private static async Task StartStreamingChatAsync(IChatCompletion chatCompletion)
    {
        bool roleWritten = false;
        var prompt = "Hi, I'm looking for book suggestions";

        Console.WriteLine($"User: {prompt}");
        Console.WriteLine("------------------------");
        await foreach (var chatUpdate in chatCompletion.GetStreamingContentAsync<StreamingChatContent>(prompt))
        {
            if (!roleWritten && chatUpdate.Role.HasValue)
            {
                Console.Write($"{chatUpdate.Role.Value}: {chatUpdate.Content}\n");
                roleWritten = true;
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                Console.Write(chatUpdate.Content);
            }
        }

        Console.WriteLine("\n------------------------");
    }
}
