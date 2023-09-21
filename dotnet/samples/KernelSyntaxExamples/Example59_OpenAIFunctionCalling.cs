// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.Core;
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

        OpenAIRequestSettings requestSettings = new()
        {
            // Include all functions registered with the kernel.
            // Alternatively, you can provide your own list of OpenAIFunctions to include.
            Functions = kernel.Functions.GetFunctionViews().Select(f => f.ToOpenAIFunction()).ToList(),
        };

        // Set FunctionCall to the name of a specific function to force the model to use that function.
        requestSettings.FunctionCall = "Date";
        await CompleteChatWithFunctionsAsync("What day is today?", chatHistory, chatCompletion, kernel, requestSettings);

        // Set FunctionCall to auto to let the model choose the best function to use.
        requestSettings.FunctionCall = OpenAIRequestSettings.FunctionCallAuto;
        await CompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletion, kernel, requestSettings);
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
        kernel.ImportSemanticPluginFromDirectory(folder, "SummarizePlugin");
        kernel.ImportSemanticPluginFromDirectory(folder, "WriterPlugin");
        kernel.ImportSemanticPluginFromDirectory(folder, "FunPlugin");
        kernel.ImportPlugin(new TimePlugin(), "TimePlugin");

        await kernel.ImportAIPluginAsync("KlarnaShoppingPlugin", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), new OpenApiPluginExecutionParameters());

        return kernel;
    }

    private static async Task CompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, IKernel kernel, OpenAIRequestSettings requestSettings)
    {
        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);

        // Send request
        var chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];

        // Check for message response
        var chatMessage = await chatResult.GetChatMessageAsync();
        if (!string.IsNullOrEmpty(chatMessage.Content))
        {
            Console.WriteLine(chatMessage.Content);
        }

        // Check for function response
        OpenAIFunctionResponse? functionResponse = chatResult.GetFunctionResponse();
        if (functionResponse is not null)
        {
            // Print function response details
            Console.WriteLine("Function name: " + functionResponse.FunctionName);
            Console.WriteLine("Plugin name: " + functionResponse.PluginName);
            Console.WriteLine("Arguments: ");
            foreach (var parameter in functionResponse.Parameters)
            {
                Console.WriteLine($"- {parameter.Key}: {parameter.Value}");
            }

            // If the function returned by OpenAI is an SKFunction registered with the kernel,
            // you can invoke it using the following code.
            if (kernel.Functions.TryGetFunctionAndContext(functionResponse, out ISKFunction? func, out ContextVariables? context))
            {
                var result = await kernel.RunAsync(func, context).ConfigureAwait(false);
                Console.WriteLine(result.Result);
            }
            else
            {
                Console.WriteLine($"Error: Function {functionResponse.PluginName}.{functionResponse.FunctionName} not found.");
            }
        }
    }
}
