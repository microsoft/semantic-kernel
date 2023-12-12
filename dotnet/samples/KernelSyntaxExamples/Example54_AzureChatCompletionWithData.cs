// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

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

        await ExampleWithChatCompletionAsync();
        await ExampleWithKernelAsync();
    }

    private static async Task ExampleWithChatCompletionAsync()
    {
        Console.WriteLine("=== Example with Chat Completion ===");

        var chatCompletion = new AzureOpenAIChatCompletionWithDataService(GetCompletionWithDataConfig());
        var chatHistory = new ChatHistory();

        // First question without previous context based on uploaded content.
        var ask = "How did Emily and David meet?";
        chatHistory.AddUserMessage(ask);

        // Chat Completion example
        var chatMessage = (AzureOpenAIWithDataChatMessageContent)await chatCompletion.GetChatMessageContentAsync(chatHistory);

        var response = chatMessage.Content!;
        var toolResponse = chatMessage.ToolContent;

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response}");
        Console.WriteLine();

        // Chat history maintenance
        if (!string.IsNullOrEmpty(toolResponse))
        {
            chatHistory.AddMessage(AuthorRole.Tool, toolResponse);
        }

        chatHistory.AddAssistantMessage(response);

        // Second question based on uploaded content.
        ask = "What are Emily and David studying?";
        chatHistory.AddUserMessage(ask);

        // Chat Completion Streaming example
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine("Response: ");

        await foreach (var word in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            Console.Write(word);
        }

        Console.WriteLine(Environment.NewLine);
    }

    private static async Task ExampleWithKernelAsync()
    {
        Console.WriteLine("=== Example with Kernel ===");

        var ask = "How did Emily and David meet?";

        var completionWithDataConfig = GetCompletionWithDataConfig();

        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(config: completionWithDataConfig)
            .Build();

        var function = kernel.CreateFunctionFromPrompt("Question: {{$input}}");

        // First question without previous context based on uploaded content.
        var response = await kernel.InvokeAsync(function, new() { ["input"] = ask });

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response.GetValue<string>()}");
        Console.WriteLine();

        // Second question based on uploaded content.
        ask = "What are Emily and David studying?";
        response = await kernel.InvokeAsync(function, new() { ["input"] = ask });

        // Output
        // Ask: What are Emily and David studying?
        // Response: They are passionate scientists who study glaciology,
        // a branch of geology that deals with the study of ice and its effects.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response.GetValue<string>()}");
        Console.WriteLine();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatCompletionWithDataConfig"/> class.
    /// </summary>
    private static AzureOpenAIChatCompletionWithDataConfig GetCompletionWithDataConfig()
    {
        return new AzureOpenAIChatCompletionWithDataConfig
        {
            CompletionModelId = TestConfiguration.AzureOpenAI.ChatDeploymentName,
            CompletionEndpoint = TestConfiguration.AzureOpenAI.Endpoint,
            CompletionApiKey = TestConfiguration.AzureOpenAI.ApiKey,
            DataSourceEndpoint = TestConfiguration.AzureAISearch.Endpoint,
            DataSourceApiKey = TestConfiguration.AzureAISearch.ApiKey,
            DataSourceIndex = TestConfiguration.AzureAISearch.IndexName
        };
    }
}
