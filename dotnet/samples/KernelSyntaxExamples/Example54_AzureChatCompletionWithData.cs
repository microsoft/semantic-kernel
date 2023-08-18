// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/**
 * This example shows how to use Azure OpenAI Chat Completion with data.
 * More information: https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart
 */
// ReSharper disable once InconsistentNaming
public static class Example54_AzureChatCompletionWithData
{
    public static async Task RunAsync()
    {
        var chatCompletion = GetChatCompletion();
        var chatHistory = chatCompletion.CreateNewChat();

        // Uploaded content in Azure Blob Storage in .txt file:

        // Emily and David, two passionate scientists, met during a research expedition to Antarctica.
        // Bonded by their love for the natural world and shared curiosity,
        // they uncovered a groundbreaking phenomenon in glaciology that could
        // potentially reshape our understanding of climate change.

        // First message without previous context - question based on uploaded content.
        chatHistory.AddUserMessage("How did Emily and David meet?");

        // Completion example
        string reply = await chatCompletion.GenerateMessageAsync(chatHistory);

        // Output: Emily and David, both passionate scientists, met during a research expedition to Antarctica [doc1].
        Console.WriteLine(reply);
        Console.Write(Environment.NewLine);

        // Second message
        chatHistory.AddUserMessage("What did they find?");

        // Completion streaming example
        await foreach (var message in chatCompletion.GenerateMessagesStreamAsync(chatHistory))
        {
            // Output:
            // Emily and David uncovered a groundbreaking phenomenon in
            // glaciology that could potentially reshape our understanding
            // of climate change during their research expedition to Antarctica [doc1].[DONE]
            Console.Write(message);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureChatCompletionWithData"/> class with completion configuration.
    /// </summary>
    private static AzureChatCompletionWithData GetChatCompletion()
    {
        return new(new AzureChatCompletionWithDataConfig
        {
            CompletionModelId = TestConfiguration.AzureOpenAI.ChatDeploymentName,
            CompletionEndpoint = TestConfiguration.AzureOpenAI.Endpoint,
            CompletionApiKey = TestConfiguration.AzureOpenAI.ApiKey,
            DataSourceEndpoint = TestConfiguration.ACS.Endpoint,
            DataSourceApiKey = TestConfiguration.ACS.ApiKey,
            DataSourceIndex = TestConfiguration.ACS.IndexName
        });
    }
}
