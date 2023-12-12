// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.OpenApi;

#pragma warning disable CA1812 // Uninstantiated internal types

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
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Plugins.AddFromType<TimePlugin>();
        builder.Plugins.AddFromType<WidgetPlugin>();
        builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
        builder.Services.AddLogging(services => services.AddConsole().SetMinimumLevel(LogLevel.Trace));
        Kernel kernel = builder.Build();

        // Load additional functions into the kernel
        await kernel.ImportPluginFromOpenAIAsync("KlarnaShoppingPlugin", new Uri("https://www.klarna.com/.well-known/ai-plugin.json"));

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory();
        var executionSettings = new OpenAIPromptExecutionSettings();

        // Set FunctionCall to the result of FunctionCallBehavior.RequireFunction with a specific function to force the model to use that function.
        executionSettings.FunctionCallBehavior = FunctionCallBehavior.RequireFunction(kernel.Plugins["TimePlugin"]["Date"].Metadata.ToOpenAIFunction(), autoInvoke: true);
        await CompleteChatWithFunctionsAsync("What day is today?", chatHistory, chatCompletionService, kernel, executionSettings);

        // Set FunctionCall to FunctionCallBehavior.ProvideKernelFunctions to let the model choose the best function to use from all available in the kernel.
        executionSettings.FunctionCallBehavior = FunctionCallBehavior.AutoInvokeKernelFunctions;
        await CompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletionService, kernel, executionSettings);

        // Reset chat history to avoid Token Limit Exceeded error (4K Context Models)
        chatHistory = new ChatHistory();
        await StreamingCompleteChatWithFunctionsAsync("What computer tablets are available for under $200?", chatHistory, chatCompletionService, kernel, executionSettings);

        // This sample relies on the AI picking the correct color from an enum
        executionSettings.FunctionCallBehavior = FunctionCallBehavior.RequireFunction(kernel.Plugins["WidgetPlugin"]["CreateWidget"].Metadata.ToOpenAIFunction(), autoInvoke: true);
        await CompleteChatWithFunctionsAsync("Create a lime widget called foo", chatHistory, chatCompletionService, kernel, executionSettings);
        await CompleteChatWithFunctionsAsync("Create a scarlet widget called bar", chatHistory, chatCompletionService, kernel, executionSettings);
    }

    private static async Task CompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletionService chatCompletionService, Kernel kernel, OpenAIPromptExecutionSettings executionSettings)
    {
        Console.WriteLine($"\n\n======== Non-Streaming - {executionSettings.FunctionCallBehavior} ========\n");

        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);
        chatHistory.Add(await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel));
        Console.WriteLine($"Assistant response: {chatHistory[chatHistory.Count - 1].Content}");
    }

    private static async Task StreamingCompleteChatWithFunctionsAsync(string ask, ChatHistory chatHistory, IChatCompletionService chatCompletionService, Kernel kernel, OpenAIPromptExecutionSettings executionSettings)
    {
        Console.WriteLine($"\n\n======== Streaming - {executionSettings.FunctionCallBehavior} ========\n");
        Console.WriteLine($"User message: {ask}");
        chatHistory.AddUserMessage(ask);

        // Send request
        var fullContent = new List<StreamingChatMessageContent>();
        Console.Write("Assistant response: ");
        await foreach (var chatResult in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel))
        {
            fullContent.Add(chatResult);
            if (chatResult.Content is { Length: > 0 })
            {
                Console.Write(chatResult.Content);
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
