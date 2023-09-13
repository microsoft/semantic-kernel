// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
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

        var chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];

        var chatMessage = await chatResult.GetChatMessageAsync();
        if (chatMessage.Content.IsNotNullOrEmpty())
        {
            Console.WriteLine(chatMessage.Content);
        }

        var functionCall = chatResult.ModelResult.GetResult<ChatModelResult>().Choice.Message.FunctionCall;
        if (functionCall is not null)
        {
            Console.WriteLine("Function name:" + functionCall.Name);
            Console.WriteLine("Function args: " + functionCall.Arguments);

            FunctionCallResponse functionResponse = FunctionCallResponse.FromFunctionCall(functionCall);

            // Validate and retrieve function - move this somewhere else?
            // TODO: handle global skills
            try
            {
                var context = kernel.CreateNewContext();
                var func = context.Skills!.GetFunction(functionResponse.SkillName, functionResponse.FunctionName);

                foreach (var parameter in functionResponse.Parameters)
                {
                    // add to context
                    // todo: could determine type of each param? or have dictionary store strings
                    // todo:" use tostring or json serialization?
                    context.Variables.Set(parameter.Key, JsonSerializer.Serialize(parameter.Value));
                }
                var result = await func.InvokeAsync(context);
                Console.WriteLine(result.Result);
            }
            catch (SKException)
            {
                // Invalid function call
            }
        }
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
