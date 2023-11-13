// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Azure.Identity;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example65_LMStudio
{
    public static async Task RunAsync()
    {
        var modelId = "local";
        var uri = new Uri("http://localhost:1234");
        var openAIClient = new OpenAIClient(uri, new InteractiveBrowserCredential());

        // Create logger factory with default level as warning
        using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
        {
            builder
                .SetMinimumLevel(LogLevel.Warning)
                .AddConsole();
        });

        var chatCompletion = new OpenAIChatCompletion(modelId, openAIClient, loggerFactory);
        var chatHistory = chatCompletion.CreateNewChat();
        chatHistory.AddSystemMessage("Always answer in rhymes.");
        chatHistory.AddUserMessage("ntroduce yourself.");

        // Run
        var chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory))[0];
        var chatMessage = await chatResult.GetChatMessageAsync();
        Console.WriteLine(chatMessage.Content);
    }
}
