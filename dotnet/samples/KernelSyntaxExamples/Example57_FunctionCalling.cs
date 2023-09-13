// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Skills.Core;
using RepoUtils;

/**
 * This example shows how to use OpenAI's function calling capability via the chat completions interface.
 */

// ReSharper disable once InconsistentNaming
public static class Example57_FunctionCalling
{
    public static async Task RunAsync()
    {
        IKernel kernel = InitializeKernel();

        await UseChatCompletionInterfaceAsync(kernel);
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

        ChatRequestSettings requestSettings = new();
        requestSettings.Functions = kernel.Skills.GetFunctionsView();

        var result = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];

        // TODO: how to determine if result is chat message vs. function?
        var functionCall = result.ModelResult.GetResult<ChatModelResult>().Choice.Message.FunctionCall; // this is AzureSdk specific
        if (functionCall is not null)
        {
            Console.WriteLine("Function name:" + functionCall.Name);
            Console.WriteLine("Function args: " + functionCall.Arguments);

            //var context = kernel.CreateNewContext();
            //var func = context.Skills!.GetFunction(functionCall.Name);
            //foreach (var arg in functionCall.Arguments) // todo parse
            //{
            //    // add to context
            //    context.Variables.Set(arg.ke)
            //}
            //var result = func.InvokeAsync(context);
            //var result = kernel.RunAsync(func, context);
        }

        // TODO: expose FunctionCall object in ChatMessage?
        var chatMessage = await result.GetChatMessageAsync();
        Console.WriteLine(chatMessage.Content);
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
