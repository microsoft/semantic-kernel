// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using RepoUtils;

/**
 * This example shows how to use OpenAI's function calling capability via the chat completions interface.
 */

// ReSharper disable once InconsistentNaming
public static class Example58_FunctionCalling
{
    public static async Task RunAsync()
    {
        IKernel kernel = await InitializeKernelAsync();
        var chatCompletion = kernel.GetService<IChatCompletion>();
        var chatHistory = chatCompletion.CreateNewChat();

        await CompleteChatWithFunctionsAsync("What day is today?", chatHistory, chatCompletion, kernel);

        await CompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletion, kernel);
    }

    private static async Task<IKernel> InitializeKernelAsync()
    {
        // Create kernel with chat completions service
        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey, serviceId: "chat")
            //.WithAzureChatCompletionService(TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ApiKey, serviceId: "chat")
            .Build();

        // Load functions to kernel
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        kernel.ImportSkill(new TimeSkill(), "TimeSkill");

        await kernel.ImportAIPluginAsync("KlarnaShoppingPlugin", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), new OpenApiSkillExecutionParameters());

        return kernel;
    }

    private static async Task CompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, IKernel kernel)
    {
        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);

        // Retrieve available functions from the kernel and add to request settings
        ChatRequestSettings requestSettings = new();
        requestSettings.Functions = kernel.Skills.GetFunctionsView();

        // Send request
        var chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];

        // Check for message response
        var chatMessage = await chatResult.GetChatMessageAsync();
        if (chatMessage.Content.IsNotNullOrEmpty())
        {
            Console.WriteLine(chatMessage.Content);
        }

        // Check for function response
        var functionCall = chatResult.ModelResult.GetResult<ChatModelResult>().Choice.Message.FunctionCall;
        if (functionCall is not null)
        {
            FunctionCallResponse functionResponse = FunctionCallResponse.FromFunctionCall(functionCall);

            Console.WriteLine("Skill name: " + functionResponse.SkillName);
            Console.WriteLine("Function name: " + functionResponse.FunctionName);
            Console.WriteLine("Arguments: ");

            // Validate and retrieve function - move this somewhere else?
            // TODO: handle global skills
            try
            {
                var context = kernel.CreateNewContext();
                var func = context.Skills!.GetFunction(functionResponse.SkillName, functionResponse.FunctionName);

                foreach (var parameter in functionResponse.Parameters)
                {
                    Console.WriteLine($"- {parameter.Key}: {parameter.Value}");

                    // Add to parameters to context
                    context.Variables.Set(parameter.Key, parameter.Value.ToString());
                }

                // Invoke the function
                var result = await func.InvokeAsync(context);
                Console.WriteLine(result.Result);
            }
            catch (SKException)
            {
                // Invalid function call
            }
        }
    }
}
