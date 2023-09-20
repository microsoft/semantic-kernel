// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;


/// <summary>
///  Examples demonstrating how to pass FunctionDefinitions with ChatCompletions 
/// </summary>
public static class Example56_OpenAIChatCompletionWithFunctionCalling
{
    public static async Task RunAsync()
    {
        await RunChatAsync();
        await RunChatWithResponse();
        await RunAsSKFunctionCall();
    }


    /// <summary>
    ///  Demonstrates how to use the Azure OpenAI chat completion service with function calling and a raw json response
    /// </summary>
    private static async Task RunChatAsync()
    {
        var builder = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);

        IKernel kernel = builder.Build();
        IChatCompletion chatCompletion = kernel.GetService<IChatCompletion>();
        var chatHistory = chatCompletion.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book 3 different book suggestions about sci-fi");

        var chatRequestSettings = new OpenAIRequestSettings()
        {
            MaxTokens = 1024,
            ResultsPerPrompt = 2,
            Temperature = 1,
            TopP = 0.5,
            FrequencyPenalty = 0
        };

        // First bot assistant message as a json response
        var functionCallResponse = await chatCompletion.GenerateFunctionCallAsync(chatHistory, chatRequestSettings, new[] { SuggestBooks, SuggestVacationDestinations });
        Console.WriteLine(functionCallResponse);
        Console.WriteLine();
    }


    /// <summary>
    ///  Demonstrates how to use the Azure OpenAI chat completion service with function calling and a structured response
    /// </summary>
    private static async Task RunChatWithResponse()
    {

        var builder = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);

        IKernel kernel = builder.Build();
        IChatCompletion chatCompletion = kernel.GetService<IChatCompletion>();

        var chatHistory = chatCompletion.CreateNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book 3 different book suggestions about sci-fi");

        var functionCallRequestSettings = new FunctionCallRequestSettings()
        {
            MaxTokens = 1024,
            ResultsPerPrompt = 2,
            Temperature = 1,
            TopP = 0.5,
            FrequencyPenalty = 0,
            CallableFunctions = new List<FunctionDefinition>(new[] { SuggestBooks, SuggestVacationDestinations })
        };

        // First bot assistant message as a json response
        List<string>? bookRecommendations = await chatCompletion.GenerateResponseAsync<List<string>>(chatHistory, functionCallRequestSettings);

        if (bookRecommendations != null)
        {
            Console.WriteLine("Book recommendations:");
            Console.WriteLine(string.Join(", \n", bookRecommendations));
        }
        Console.WriteLine();
    }


    /// <summary>
    /// Demonstrates how to use the Azure OpenAI chat completion service with function calling and execute the function call
    /// </summary>
    private static async Task RunAsSKFunctionCall()
    {
        var builder = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);

        string folder = RepoFiles.SampleSkillsPath();

        IKernel kernel = builder.Build();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        //We're going to ask the planner to find a function to achieve this goal.
        var goal = "Write a joke about Cleopatra in the style of Hulk Hogan.";

        ISKFunction functionCall = kernel.CreateFunctionCall(goal, callFunctionsAutomatically: true, maxTokens: 1024);
        var context = kernel.CreateNewContext();
        var result = await functionCall.InvokeAsync(context);
        Console.WriteLine("Result: ");
        Console.WriteLine(result.Result);
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
