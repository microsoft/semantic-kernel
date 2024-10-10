// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
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
        var result1 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result1);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather like in Marseille?"));
        var result2 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result1);
        Console.WriteLine(result2);
    }

    [Fact]
    public async Task AutoInvokeKernelFunctionsWithComplexParameterAsync()
    {
        // Create a kernel with MistralAI chat completion and HolidayPlugin
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

    [Fact]
    public async Task AutoInvokeLightPluginAsync()
    {
        // Create a kernel with OpenAI chat completion and LightPlugin
        Kernel kernel = CreateKernelWithPlugin<LightPlugin>();
        kernel.FunctionInvocationFilters.Add(new FunctionFilterExample(this.Output));

        // Invoke chat prompt with auto invocation of functions enabled
        const string ChatPrompt = """
            <message role="user">Turn on the light?</message>
        """;
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(
            ChatPrompt, executionSettings);
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        Console.WriteLine(chatPromptResult);
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => $"12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy\nLocation: {location}";
    }

    private sealed class HolidayPlugin
    {
        [KernelFunction]
        [Description("Book a holiday for a specified time period.")]
        public string BookHoliday(
            [Description("Holiday time period")] HolidayRequest holidayRequest
        ) => $"Holiday booked, starting {holidayRequest.StartDate} and ending {holidayRequest.EndDate}";
    }

    private sealed class HolidayRequest
    {
        [Description("The date when the holiday period starts in ISO 8601 format")]
        public string StartDate { get; set; } = string.Empty;

        [Description("The date when the holiday period ends in ISO 8601 format")]
        public string EndDate { get; set; } = string.Empty;
    }

    private sealed class LightPlugin
    {
        public bool IsOn { get; set; } = false;

        [KernelFunction]
        [Description("Gets the state of the light.")]
        public string GetState() => IsOn ? "on" : "off";

        [KernelFunction]
        [Description("Changes the state of the light.'")]
        public string ChangeState(bool newState)
        {
            this.IsOn = newState;
            var state = GetState();
            return state;
        }
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

    private sealed class FunctionFilterExample(ITestOutputHelper output) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            output.WriteLine($"Function {context.Function.Name} is being invoked with arguments: {JsonSerializer.Serialize(context.Arguments)}");

            await next(context);
        }
    }
}
