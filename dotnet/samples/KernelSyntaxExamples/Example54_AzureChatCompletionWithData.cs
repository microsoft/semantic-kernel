// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/**
 * This example shows how to use Azure OpenAI Chat Completion with data.
 * More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
 */
// ReSharper disable once InconsistentNaming
public static class Example54_AzureChatCompletionWithData
{
    public static async Task RunAsync()
    {
        // Uploaded content in Azure Blob Storage in .txt file:

        // Emily and David, two passionate scientists, met during a research expedition to Antarctica.
        // Bonded by their love for the natural world and shared curiosity,
        // they uncovered a groundbreaking phenomenon in glaciology that could
        // potentially reshape our understanding of climate change.

        await ExampleWithChatCompletion();
        await ExampleWithKernel();
    }

    private static async Task ExampleWithChatCompletion()
    {
        Console.WriteLine("=== Example with Chat Completion ===");

        var chatCompletion = new AzureChatCompletionWithData(GetCompletionWithDataConfig());
        var chatHistory = chatCompletion.CreateNewChat();

        // First question without previous context based on uploaded content.
        chatHistory.AddUserMessage("How did Emily and David meet?");

        // Chat Completion example
        string reply = await chatCompletion.GenerateMessageAsync(chatHistory);

        // Output: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine(reply);
        Console.Write(Environment.NewLine);

        // Second question based on uploaded content.
        chatHistory.AddUserMessage("What are Emily and David studying?");

        // Chat Completion Streaming example
        await foreach (var result in chatCompletion.GetStreamingChatCompletionsAsync(chatHistory))
        {
            await foreach (var message in result.GetStreamingChatMessageAsync())
            {
                // Output:
                // They are passionate scientists who study glaciology,
                // a branch of geology that deals with the study of ice and its effects.
                Console.Write(message.Content);
            }
        }

        Console.WriteLine(Environment.NewLine);
    }

    private static async Task ExampleWithKernel()
    {
        Console.WriteLine("=== Example with Kernel ===");

        var completionWithDataConfig = GetCompletionWithDataConfig();

        IKernel kernel = new KernelBuilder()
            .WithAzureChatCompletionService(config: completionWithDataConfig)
            .Build();

        var semanticFunction = kernel.CreateSemanticFunction("Question: {{$input}}");

        // First question without previous context based on uploaded content.
        var result = await kernel.RunAsync("How did Emily and David meet?", semanticFunction);

        // Output: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine(result);
        Console.WriteLine();

        // Second question based on uploaded content.
        result = await kernel.RunAsync("What are Emily and David studying?", semanticFunction);

        // Output:
        // They are passionate scientists who study glaciology,
        // a branch of geology that deals with the study of ice and its effects.
        Console.WriteLine(result);

        Console.WriteLine(Environment.NewLine);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureChatCompletionWithDataConfig"/> class.
    /// </summary>
    private static AzureChatCompletionWithDataConfig GetCompletionWithDataConfig()
    {
        return new AzureChatCompletionWithDataConfig
        {
            CompletionModelId = TestConfiguration.AzureOpenAI.ChatDeploymentName,
            CompletionEndpoint = TestConfiguration.AzureOpenAI.Endpoint,
            CompletionApiKey = TestConfiguration.AzureOpenAI.ApiKey,
            DataSourceEndpoint = TestConfiguration.ACS.Endpoint,
            DataSourceApiKey = TestConfiguration.ACS.ApiKey,
            DataSourceIndex = TestConfiguration.ACS.IndexName
        };
    }
}
