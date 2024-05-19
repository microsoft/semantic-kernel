// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;
public sealed class OpenAI_FunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task AutoInvokeKernelFunctionsAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();

        // Invoke chat prompt with auto invocation of functions enabled
        const string ChatPrompt = """
            <message role="user">What is the weather like in Paris?</message>
        """;
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(
            ChatPrompt, executionSettings);
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        Console.WriteLine(chatPromptResult);
    }

    [Fact]
    public async Task AutoInvokeKernelFunctionsMultipleCallsAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result1 = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);
        chatHistory.AddRange(result1);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather like in Marseille?"));
        var result2 = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result1[0].Content);
        Console.WriteLine(result2[0].Content);
    }

    [Fact]
    public async Task AutoInvokeKernelFunctionsWithComplexParameterAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<HolidayPlugin>();

        // Invoke chat prompt with auto invocation of functions enabled
        const string ChatPrompt = """
            <message role="user">Book a holiday for me from 6th June 2025 to 20th June 2025?</message>
        """;
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(
            ChatPrompt, executionSettings);
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        Console.WriteLine(chatPromptResult);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => "12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy";
    }

    public sealed class HolidayPlugin
    {
        [KernelFunction]
        [Description("Book a holiday for a specified time period.")]
        public string BookHoliday(
            [Description("The city and department, e.g. Marseille, 13")] HolidayRequest holidayRequest
        ) => $"Holiday booked, starting {holidayRequest.StartDate} and ending {holidayRequest.EndDate}";
    }

    public sealed class HolidayRequest
    {
        [Description("The date when the holiday period starts in ISO 8601 format")]
        public string StartDate { get; set; } = string.Empty;

        [Description("The date when the holiday period ends in ISO 8601 format")]
        public string EndDate { get; set; } = string.Empty;
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
