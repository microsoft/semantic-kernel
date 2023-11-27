// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/**
 * The following example shows how to use Semantic Kernel with streaming Multiple Results Chat Completion
 */
// ReSharper disable once InconsistentNaming
public static class Example37_MultiStreamingCompletion
{
    public static async Task RunAsync()
    {
        await AzureOpenAIMultiChatCompletionStreamAsync();
        await OpenAIChatCompletionStreamAsync();
    }

    private static async Task AzureOpenAIMultiChatCompletionStreamAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion - Raw Streaming ========");

        var chatCompletion = new AzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await ChatCompletionStreamAsync(chatCompletion);
    }

    private static async Task OpenAIChatCompletionStreamAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Chat Completion - Raw Streaming ========");

        IChatCompletion chatCompletion = new OpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        await ChatCompletionStreamAsync(chatCompletion);
    }

    private static async Task ChatCompletionStreamAsync(IChatCompletion chatCompletion)
    {
        var requestSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 3
        };

        await foreach (var chatUpdate in chatCompletion.GetStreamingContentAsync<string>("Write one paragraph about why AI is awesome"))
        {
            Console.Write(chatUpdate);
        }

        Console.WriteLine();
    }
}
