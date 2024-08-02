// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
///  Sample shows how to the model will reuse a function result from the chat history.
/// </summary>
public sealed class OpenAI_RepeatedFunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Sample shows a chat history where each ask requires a function to be called but when
    /// an ask is repeated the model will reuse the previous function result.
    /// </summary>
    [Fact]
    public async Task ReuseFunctionResultExecutionAsync()
    {
        // Create a kernel with OpenAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Boston?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result1 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result1);
        Console.WriteLine(result1);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?"));
        var result2 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result2);
        Console.WriteLine(result2);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather like in Dublin?"));
        var result3 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result3);
        Console.WriteLine(result3);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather like in Boston?"));
        var result4 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result4);
        Console.WriteLine(result4);
    }
    private sealed class WeatherPlugin
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
