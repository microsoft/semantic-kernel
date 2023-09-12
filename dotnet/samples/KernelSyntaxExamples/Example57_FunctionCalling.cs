// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Core;
using RepoUtils;

/**
 * This example shows how to use Stepwise Planner to create and run a stepwise plan for a given goal.
 */

// ReSharper disable once InconsistentNaming
public static class Example57_FunctionCalling
{
    public static async Task RunAsync()
    {
        IKernel kernel = InitializeKernel();

        await UseChatCompletionInterfaceAsync(kernel);

        //await UsePlannerAsync(kernel);
    }

    public static IKernel InitializeKernel()
    {
        // Create kernel with chat completions service
        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey, serviceId: "chat")
            //.WithAzureChatCompletionService(TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ApiKey, serviceId: "chat")
            .Build();

        // Load functions
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        kernel.ImportSkill(new TimeSkill(), "time");

        return kernel;
    }

    public static async Task UseChatCompletionInterfaceAsync(IKernel kernel)
    {
        var chatCompletion = kernel.GetService<IChatCompletion>();
        var chatHistory = chatCompletion.CreateNewChat();

        chatHistory.AddUserMessage("What day is today?");
        //chatHistory.AddUserMessage("Tell me a joke!");

        var result = (await chatCompletion.GetChatCompletionsAsync(
            chatHistory,
            functions: kernel.Skills.GetFunctionsView()
        ))[0];
        var chatMessage = await result.GetChatMessageAsync();

        // results[0].ModelResult.result.Choice.Message.FunctionCall.[Arguments|Name]

        //Console.WriteLine(chatMessage.Content);
    }

    public static async Task UsePlannerAsync(IKernel kernel)
    {

    }

    private static AzureChatCompletion GetAzureChatCompletion()
    {
        return new(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);
    }

    private static OpenAIChatCompletion GetOpenAIChatCompletion()
    {
        return new OpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);
    }
}
