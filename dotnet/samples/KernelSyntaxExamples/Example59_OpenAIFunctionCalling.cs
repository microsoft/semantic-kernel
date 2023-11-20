// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;
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
        Kernel kernel = await InitializeKernelAsync();
        var chatCompletion = kernel.GetService<IChatCompletion>();
        var chatHistory = chatCompletion.CreateNewChat();

        OpenAIRequestSettings requestSettings = new()
        {
            // Include all functions registered with the kernel.
            // Alternatively, you can provide your own list of OpenAIFunctions to include.
            Functions = kernel.Plugins.GetFunctionsMetadata().Select(f => f.ToOpenAIFunction()).ToList(),
            FunctionCall = "TimePlugin_Date",
        };

        // Set FunctionCall to the name of a specific function to force the model to use that function.
        await CompleteChatWithFunctionsAsync("What day is today?", chatHistory, chatCompletion, kernel, requestSettings);

        // Before each invocation I need to specify the function call I want to use.
        requestSettings.FunctionCall = "TimePlugin_Date";
        await StreamingCompleteChatWithFunctionsAsync("What day is today?", chatHistory, chatCompletion, kernel, requestSettings);

        // Set FunctionCall to auto to let the model choose the best function to use.
        requestSettings.FunctionCall = OpenAIRequestSettings.FunctionCallAuto;
        await CompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletion, kernel, requestSettings);

        requestSettings.FunctionCall = OpenAIRequestSettings.FunctionCallAuto;
        await StreamingCompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletion, kernel, requestSettings);

        // This sample relies on the AI picking the correct color from an enum
        requestSettings.FunctionCall = "WidgetPlugin_CreateWidget";
        await CompleteChatWithFunctionsAsync("Create a lime widget called foo", chatHistory, chatCompletion, kernel, requestSettings);

        requestSettings.FunctionCall = "WidgetPlugin_CreateWidget";
        await CompleteChatWithFunctionsAsync("Create a scarlet widget called bar", chatHistory, chatCompletion, kernel, requestSettings);
    }

    private static async Task<Kernel> InitializeKernelAsync()
    {
        // Create kernel with chat completions service
        Kernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey, serviceId: "chat")
            //.WithAzureOpenAIChatCompletionService(TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ApiKey, serviceId: "chat")
            .Build();

        // Load functions to kernel
        kernel.ImportPluginFromObject<TimePlugin>("TimePlugin");
        kernel.ImportPluginFromObject(new WidgetPlugin(), "WidgetPlugin");
        await kernel.ImportPluginFromOpenAIAsync("KlarnaShoppingPlugin", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), new OpenAIFunctionExecutionParameters());

        return kernel;
    }

    private static async Task CompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, Kernel kernel, OpenAIRequestSettings requestSettings)
    {
        Console.WriteLine($"\n\n======== Function Call - {(requestSettings.FunctionCall == OpenAIRequestSettings.FunctionCallAuto ? "Automatic" : "Specific (TimePlugin.Date)")} ========\n");
        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);

        // Send request and add response to chat history
        var chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];
        chatHistory.AddAssistantMessage(chatResult);

        await PrintChatResultAsync(chatResult);

        // Check for function response
        OpenAIFunctionResponse? functionResponse = chatResult.GetOpenAIFunctionResponse();
        if (functionResponse is not null)
        {
            // If the function returned by OpenAI is an SKFunction registered with the kernel,
            // you can invoke it using the following code.
            if (kernel.Plugins.TryGetFunctionAndContext(functionResponse, out ISKFunction? func, out ContextVariables? context))
            {
                var result = (await kernel.RunAsync(func, context)).GetValue<object>();

                string? resultContent = null;
                if (result is RestApiOperationResponse apiResponse)
                {
                    resultContent = apiResponse.Content?.ToString();
                }
                else if (result is string str)
                {
                    resultContent = str;
                }

                if (!string.IsNullOrEmpty(resultContent))
                {
                    // Add the function result to chat history
                    chatHistory.AddFunctionMessage(resultContent, functionResponse.FullyQualifiedName);
                    Console.WriteLine($"Function response: {resultContent}");

                    // Get another completion
                    requestSettings.FunctionCall = OpenAIRequestSettings.FunctionCallNone;
                    chatResult = (await chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings))[0];
                    chatHistory.AddAssistantMessage(chatResult);

                    await PrintChatResultAsync(chatResult);
                }
            }
            else
            {
                Console.WriteLine($"Error: Function {functionResponse.PluginName}.{functionResponse.FunctionName} not found.");
            }
        }
    }

    private static async Task PrintChatResultAsync(IChatResult chatResult)
    {
        // Check for message response
        var chatMessage = await chatResult.GetChatMessageAsync();
        if (!string.IsNullOrEmpty(chatMessage.Content))
        {
            Console.WriteLine($"Assistant response: {chatMessage.Content}");
        }

        // Check for function response
        OpenAIFunctionResponse? functionResponse = chatResult.GetOpenAIFunctionResponse();
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
        }
    }

    private static async Task StreamingCompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, Kernel kernel, OpenAIRequestSettings requestSettings)
    {
        Console.WriteLine($"\n\n======== Streaming Function Call - {(requestSettings.FunctionCall == OpenAIRequestSettings.FunctionCallAuto ? "Automatic" : "Specific (TimePlugin.Date)")} ========\n");
        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);

        // Send request
        await foreach (var chatResult in chatCompletion.GetStreamingChatCompletionsAsync(chatHistory, requestSettings))
        {
            StringBuilder chatContent = new();
            Console.Write("Assistant response: ");
            await foreach (var message in chatResult.GetStreamingChatMessageAsync())
            {
                if (message.Content is not null)
                {
                    Console.Write(message.Content);
                    chatContent.Append(message.Content);
                }
            }
            chatHistory.AddAssistantMessage(chatContent.ToString());

            var functionResponse = await chatResult.GetOpenAIStreamingFunctionResponseAsync();

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
                if (kernel.Plugins.TryGetFunctionAndContext(functionResponse, out ISKFunction? func, out ContextVariables? context))
                {
                    var kernelResult = await kernel.RunAsync(func, context);

                    var result = kernelResult.GetValue<object>();

                    string? resultMessage = null;
                    if (result is RestApiOperationResponse apiResponse)
                    {
                        resultMessage = apiResponse.Content?.ToString();
                    }
                    else if (result is string str)
                    {
                        resultMessage = str;
                    }

                    if (!string.IsNullOrEmpty(resultMessage))
                    {
                        Console.WriteLine(resultMessage);

                        // Add the function result to chat history
                        chatHistory.AddAssistantMessage(resultMessage);
                    }
                }
                else
                {
                    Console.WriteLine($"Error: Function {functionResponse.PluginName}.{functionResponse.FunctionName} not found.");
                }
            }
        }
    }

    private enum WidgetColor
    {
        Red,
        Green,
        Blue
    }

    private sealed class WidgetPlugin
    {
        [SKFunction, SKName("CreateWidget"), System.ComponentModel.Description("Create a virtual widget.")]
        public string CreateWidget(
            [System.ComponentModel.Description("Widget name")] string name,
            [System.ComponentModel.Description("Widget color")] WidgetColor color
            )
        {
            return $"Created a {color} widget named {name}";
        }
    }
}
