// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;

/**
 * This example shows how to use OpenAI's function calling capability via the chat completions interface.
 * For more information, see https://platform.openai.com/docs/guides/gpt/function-calling.
 */
// ReSharper disable once InconsistentNaming
public static class Example59_OpenAIFunctionCalling
{
    public static async Task RunAsync()
    {
        // Create kernel with chat completions service and plugins
        Kernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .ConfigureServices(services =>
            {
                services.AddLogging(services => services.AddConsole().SetMinimumLevel(LogLevel.Trace));
            })
            .ConfigurePlugins(plugins =>
            {
                plugins.AddPluginFromObject<TimePlugin>();
                plugins.AddPluginFromObject<WidgetPlugin>();
            })
            .Build();

        // Load additional functions into the kernel
        await kernel.ImportPluginFromOpenAIAsync("KlarnaShoppingPlugin", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"));

        var chatCompletion = kernel.GetService<IChatCompletion>();
        var chatHistory = chatCompletion.CreateNewChat();
        var executionSettings = new OpenAIPromptExecutionSettings();

        // Set FunctionCall to the result of FunctionCallBehavior.RequireFunction with a specific function to force the model to use that function.
        executionSettings.FunctionCallBehavior = FunctionCallBehavior.RequireFunction(kernel.Plugins["TimePlugin"]["Date"].Metadata.ToOpenAIFunction(), autoInvoke: true);
        await CompleteChatWithFunctionsAsync("What day is today?", chatHistory, chatCompletion, kernel, executionSettings);

        // Set FunctionCall to FunctionCallBehavior.ProvideKernelFunctions to let the model choose the best function to use from all available in the kernel.
        executionSettings.FunctionCallBehavior = FunctionCallBehavior.AutoInvokeKernelFunctions;
        await CompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletion, kernel, executionSettings);

        await StreamingCompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletion, kernel, executionSettings);

        // This sample relies on the AI picking the correct color from an enum
        executionSettings.FunctionCallBehavior = FunctionCallBehavior.RequireFunction(kernel.Plugins["WidgetPlugin"]["CreateWidget"].Metadata.ToOpenAIFunction(), autoInvoke: true);
        await CompleteChatWithFunctionsAsync("Create a lime widget called foo", chatHistory, chatCompletion, kernel, executionSettings);
        await CompleteChatWithFunctionsAsync("Create a scarlet widget called bar", chatHistory, chatCompletion, kernel, executionSettings);
    }

    private static async Task CompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, Kernel kernel, OpenAIPromptExecutionSettings executionSettings)
    {
        Console.WriteLine($"\n\n======== Non-Streaming - {executionSettings.FunctionCallBehavior} ========\n");

        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);
        chatHistory.AddAssistantMessage((await chatCompletion.GetChatCompletionsAsync(chatHistory, executionSettings, kernel))[0]);
        Console.WriteLine($"Assistant response: {chatHistory[chatHistory.Count - 1].Content}");
    }

    private static async Task StreamingCompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletion chatCompletion, Kernel kernel, OpenAIPromptExecutionSettings executionSettings)
    {
        Console.WriteLine($"\n\n======== Streaming - {executionSettings.FunctionCallBehavior} ========\n");
        Console.WriteLine($"User message: {ask}");

        // Send request
        var fullContent = new List<StreamingChatContent>();
        Console.Write("Assistant response: ");
        await foreach (var chatResult in chatCompletion.GetStreamingContentAsync<StreamingChatContent>(ask, executionSettings, kernel))
        {
            fullContent.Add(chatResult);
            if (chatResult.ContentUpdate is { Length: > 0 })
            {
                Console.Write(chatResult.ContentUpdate);
            }
        }
        Console.WriteLine();
    }

    private enum WidgetColor
    {
        Red,
        Green,
        Blue
    }

    private sealed class WidgetPlugin
    {
        [KernelFunction, Description("Create a virtual widget.")]
        public string CreateWidget([Description("Widget name")] string name, [Description("Widget color")] WidgetColor color) =>
            $"Created a {color} widget named {name}";
    }
}
