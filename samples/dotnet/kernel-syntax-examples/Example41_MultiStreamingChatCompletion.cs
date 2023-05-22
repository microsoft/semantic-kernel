// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with Multiple Results Text Completion as streaming
 */
// ReSharper disable once InconsistentNaming
public static class Example41_MultiStreamingChatCompletion
{
    private static readonly object s_lockObject = new();

    public static async Task RunAsync()
    {
        await AzureOpenAIMultiStreamingChatCompletionAsync();
        await OpenAIMultiStreamingChatCompletionAsync();
    }

    private static async Task AzureOpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion - Raw Streaming ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddAzureChatCompletionService(
            Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        var completion = kernel.GetService<IChatCompletion>();

        await StreamingChatCompletionAsync(completion);
    }

    private static async Task OpenAIMultiStreamingChatCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Text Completion - Raw Streaming ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"), serviceId: "gpt-3.5-turbo");

        var completion = kernel.GetService<IChatCompletion>();

        await StreamingChatCompletionAsync(completion);
    }

    private static async Task StreamingChatCompletionAsync(IChatCompletion chatCompletion)
    {
        var requestSettings = new ChatRequestSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 2
        };

        var consoleLinesPerResult = 15;

        var chatHistory = (OpenAIChatHistory)chatCompletion.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for 5 random title names for sci-fi books");
        await MessageOutputAsync(chatHistory);

        PrepareDisplay();

        List<Task> resultTasks = new();
        int currentResult = 0;
        await foreach (var completionResult in chatCompletion.GetStreamingChatCompletionsAsync(chatHistory, requestSettings))
        {
            resultTasks.Add(ProcessStreamAsyncEnumerableAsync(completionResult, currentResult++, consoleLinesPerResult));
        }

        Console.WriteLine();

        await Task.WhenAll(resultTasks.ToArray());

        Console.SetCursorPosition(0, requestSettings.ResultsPerPrompt * consoleLinesPerResult);
        Console.WriteLine();
    }

    private static async Task ProcessStreamAsyncEnumerableAsync(IChatStreamingResult result, int resultNumber, int linesPerResult)
    {
        string message = string.Empty;

        await foreach (var chatMessage in result.GetChatMessageStreamingAsync())
        {
            string role = CultureInfo.CurrentCulture.TextInfo.ToTitleCase(chatMessage.Role);
            message += chatMessage.Content;

            lock (s_lockObject)
            {
                Console.SetCursorPosition(0, (resultNumber * linesPerResult));
                Console.Write($"{role}: {message}");
            }
        }
    }

    /// <summary>
    /// Break enough lines as the current console window size to display the results
    /// </summary>
    private static void PrepareDisplay()
    {
        for (int i = 0; i < Console.WindowHeight - 2; i++)
        {
            Console.WriteLine();
        }
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private static Task MessageOutputAsync(ChatHistory chatHistory)
    {
        var message = chatHistory.Messages.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");

        return Task.CompletedTask;
    }
}
