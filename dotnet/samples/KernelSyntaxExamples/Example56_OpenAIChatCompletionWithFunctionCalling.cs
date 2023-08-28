// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk.FunctionCalling;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;


/// <summary>
///  Examples demonstrating how to pass FunctionDefinitions with ChatCompletions 
/// </summary>
public static class Example56_OpenAIChatCompletionWithFunctionCalling
{
    public static async Task RunAsync()
    {
        await AzureOpenAIChatCompletionFunctionCallAsync();
        await OpenAIChatCompletionFunctionCallAsync();
        await OpenAIStructuredResponseAsync();
    }


    private static async Task AzureOpenAIChatCompletionFunctionCallAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Function Calling ========");

        AzureChatCompletion azureChatCompletion = new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await RunChatAsync(azureChatCompletion);
    }


    private static async Task AzureOpenAIStructuredResponseAsync()
    {
        Console.WriteLine("======== Open AI - Function Calling ========");

        AzureChatCompletion azureChatCompletion = new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        await RunChatWithResponse(azureChatCompletion);
    }


    private static async Task OpenAIChatCompletionFunctionCallAsync()
    {
        Console.WriteLine("======== Open AI - Function Calling ========");

        OpenAIChatCompletion openAIChatCompletion = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        await RunChatAsync(openAIChatCompletion);
    }


    private static async Task OpenAIStructuredResponseAsync()
    {
        Console.WriteLine("======== Open AI - Function Calling ========");

        OpenAIChatCompletion openAIChatCompletion = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        await RunChatWithResponse(openAIChatCompletion);
    }


    private static async Task RunChatAsync(IOpenAIChatCompletion chatCompletion)
    {
        var chatHistory = chatCompletion.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book 3 different book suggestions about sci-fi");

        var chatRequestSettings = new ChatRequestSettings
        {
            MaxTokens = 1024,
            ResultsPerPrompt = 2,
            Temperature = 1,
            TopP = 0.5,
            FrequencyPenalty = 0
        };

        // First bot assistant message as a json response
        var functionCallResponse = await chatCompletion.GenerateMessageAsync(chatHistory, chatRequestSettings, null, new[] { SuggestBooks, SuggestVacationDestinations });
        Console.WriteLine(functionCallResponse);
        Console.WriteLine();
    }


    private static async Task RunChatWithResponse(IOpenAIChatCompletion chatCompletion)
    {
        var chatHistory = chatCompletion.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book 3 different book suggestions about sci-fi");

        var chatRequestSettings = new ChatRequestSettings
        {
            MaxTokens = 1024,
            ResultsPerPrompt = 2,
            Temperature = 1,
            TopP = 0.5,
            FrequencyPenalty = 0
        };

        // First bot assistant message as a json response
        List<string>? bookRecommendations = await chatCompletion.GenerateResponseAsync<List<string>>(chatHistory, chatRequestSettings, null, new[] { SuggestBooks, SuggestVacationDestinations });

        if (bookRecommendations != null)
        {
            Console.WriteLine("Book recommendations:");
            Console.WriteLine(string.Join(", \n", bookRecommendations));
        }
        Console.WriteLine();
    }


    private static FunctionDefinition SuggestBooks => new()
    {
        Name = "suggest_books",
        Description = "Suggest 3 book titles based on the user's preferences",
        Parameters = BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Recommendations = new
                    {
                        Type = "array",
                        Description = "the titles of the recommended books",
                        Items = new
                        {
                            Type = "string"
                        }
                    }
                }
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };

    private static FunctionDefinition SuggestVacationDestinations => new()
    {
        Name = "suggest_vacation_destinations",
        Description = "Suggest vacation destinations based on the user's preferences",
        Parameters = BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Recommendations = new
                    {
                        Type = "array",
                        Description = "List of recommended vacation destinations",
                        Items = new
                        {
                            Type = "string"
                        }
                    }
                }
            }, new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };

}
