// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;

namespace ChatCompletion;

/// <summary>
/// Demonstrates the use of function calling and streaming with MistralAI.
/// </summary>
public sealed class MistralAI_StreamingFunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GetChatMessageContentsAsync()
    {
        // Create a kernel with MistralAI chat completion  and WeatherPlugin
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddMistralChatCompletion(
                modelId: TestConfiguration.MistralAI.ChatModelId!,
                apiKey: TestConfiguration.MistralAI.ApiKey!);
        kernelBuilder.Plugins.AddFromType<WeatherPlugin>();
        Kernel kernel = kernelBuilder.Build();

        // Get the chat completion service
        var chat = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What is the weather like in Paris?");

        // Get the streaming chat message contents
        var streamingChat = chat.GetStreamingChatMessageContentsAsync(
            chatHistory, new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions }, kernel);

        await foreach (var update in streamingChat)
        {
            Console.Write(update);
        }
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => "17°C\nWind: 23 KMPH\nHumidity: 59%\nMostly cloudy";
    }
}
