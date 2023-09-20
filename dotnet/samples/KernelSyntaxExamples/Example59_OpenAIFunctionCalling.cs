// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

/**
 * This example shows how to use OpenAI's function calling capability via the chat completions interface.
 * For more information, see https://platform.openai.com/docs/guides/gpt/function-calling.
 */

// ReSharper disable once InconsistentNaming
public static class Example59_OpenAIFunctionCalling
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
        kernel.ImportSkill(new TimePlugin(), "TimeSkill");

        await kernel.ImportAIPluginAsync("KlarnaShoppingPlugin", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), new OpenApiPluginExecutionParameters());

        return kernel;
    }

    private static async Task CompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, IKernel kernel)
    {
        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);

        // Retrieve available functions from the kernel and add to request settings
        OpenAIRequestSettings requestSettings = new()
        {
            Functions = kernel.Skills.GetFunctionViews().Select(f => f.ToOpenAIFunction()).ToList()
        };

        // Send request
        var chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];

        // Check for message response
        var chatMessage = await chatResult.GetChatMessageAsync();
        if (!string.IsNullOrEmpty(chatMessage.Content))
        {
            Console.WriteLine(chatMessage.Content);
        }

        // Check for function response
        OpenAIFunctionResult? functionResult = chatResult.GetFunctionResult();
        if (functionResult is not null)
        {
            Console.WriteLine("Function name: " + functionResult.FunctionName);
            Console.WriteLine("Plugin name: " + functionResult.PluginName);
            Console.WriteLine("Arguments: ");

            var context = kernel.CreateNewContext();
            if (context.Skills!.TryGetFunction(functionResult.PluginName, functionResult.FunctionName, out ISKFunction? func))
            {
                foreach (var parameter in functionResult.Parameters)
                {
                    Console.WriteLine($"- {parameter.Key}: {parameter.Value}");

                    // Add parameter to context
                    context.Variables.Set(parameter.Key, parameter.Value.ToString());
                }

                // Invoke the function
                var result = await func.InvokeAsync(context);
                Console.WriteLine(result.Result);
            }
            else
            {
                Console.WriteLine($"Error: Function {functionResult.PluginName}.{functionResult.FunctionName} not found.");
            }
        }
    }
}
