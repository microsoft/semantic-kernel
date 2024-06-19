// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// 
/// </summary>
public sealed class OpenAI_ReasonedFunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task AskingAssistantToExplainFunctionCallsAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Always include a description explaining why you want a function to be called when you request a function be called."),
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result1 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result1);
        Console.WriteLine(result1);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "Explain why you called those functions?"));
        var result2 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        Console.WriteLine(result2);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => $"12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy\nLocation: {location}";
    }

    private Kernel CreateKernelWithPlugin<T>()
    {
        // Create a logging handler to output HTTP requests and responses
        var handler = new LoggingHandler(new HttpClientHandler(), this.Output);
        HttpClient httpClient = new(handler);

        // Create a kernel with OpenAI chat completion and WeatherPlugin
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId!,
                apiKey: TestConfiguration.OpenAI.ApiKey!,
                httpClient: httpClient);
        kernelBuilder.Plugins.AddFromType<T>();
        Kernel kernel = kernelBuilder.Build();
        return kernel;
    }
}
