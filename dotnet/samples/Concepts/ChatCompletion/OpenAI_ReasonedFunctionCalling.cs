// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// Samples showing how to get the LLM to provide the reason is using function calling.
/// </summary>
public sealed class OpenAI_ReasonedFunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Using the system prompt to explain function calls doesn't work work with gpt-4o.
    /// </summary>
    [Fact]
    public async Task UseSystemPromptToExplainFunctionCallsAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Always explain why function tool calls are being used."),
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result);
        Console.WriteLine(result);
    }

    /// <summary>
    /// Asking the model to explain function calls after execution works well but may be too late depending on your use case.
    /// </summary>
    [Fact]
    public async Task AskAssistantToExplainFunctionCallsAfterExecutionAsync()
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
        Console.WriteLine(result1);

        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "Explain why you called those functions?"));
        var result2 = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        Console.WriteLine(result2);
    }

    /// <summary>
    /// Decorate each function to be called with an extra parameter which includes the reason this function needs to be called.
    /// </summary>
    [Fact]
    public async Task UseDecoratedFunctionAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<DecoratedWeatherPlugin>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result);
        Console.WriteLine(result);
    }

    /// <summary>
    /// Asking the model to explain function calls in response to each function call can work but the model may also
    /// get confused and treat the request to explain the function calls as an error response from the function calls.
    /// </summary>
    [Fact]
    public async Task AskAssistantToExplainFunctionCallsBeforeExecutionAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();
        kernel.AutoFunctionInvocationFilters.Add(new RespondExplainFunctionInvocationFilter());
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result);
        Console.WriteLine(result);
    }

    /// <summary>
    /// Asking to the model to explain function calls using a separate conversation i.e. chat history seems to provide the
    /// best results. This may be because the model can focus on explaining the function calls without being confused by other
    /// messages in the chat history.
    /// </summary>
    [Fact]
    public async Task QueryAssistantToExplainFunctionCallsBeforeExecutionAsync()
    {
        // Create a kernel with MistralAI chat completion and WeatherPlugin
        Kernel kernel = CreateKernelWithPlugin<WeatherPlugin>();
        kernel.AutoFunctionInvocationFilters.Add(new QueryExplainFunctionInvocationFilter(this.Output));
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Invoke chat prompt with auto invocation of functions enabled
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await service.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);
        chatHistory.Add(result);
        Console.WriteLine(result);
    }

    /// <summary>
    /// This <see cref="IAutoFunctionInvocationFilter"/> will respond to function call requests and ask the model to explain why it is
    /// calling the function(s). It is only suitable for transient use because it stores information about the functions that have been
    /// called for a single chat history.
    /// </summary>
    private sealed class RespondExplainFunctionInvocationFilter : IAutoFunctionInvocationFilter
    {
        private readonly HashSet<string> _functionNames = [];

        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Get the function calls for which we need an explanation
            var functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last());
            var needExplanation = 0;
            foreach (var functionCall in functionCalls)
            {
                var functionName = $"{functionCall.PluginName}-{functionCall.FunctionName}";
                if (_functionNames.Add(functionName))
                {
                    needExplanation++;
                }
            }

            if (needExplanation > 0)
            {
                // Create a response asking why these functions are being called
                context.Result = new FunctionResult(context.Result, $"Provide an explanation why you are calling function {string.Join(',', _functionNames)} and try again");
                return;
            }

            // Invoke the functions
            await next(context);
        }
    }

    /// <summary>
    /// This <see cref="IAutoFunctionInvocationFilter"/> uses the currently available <see cref="IChatCompletionService"/> to query the model
    /// to find out what certain functions are being called.
    /// </summary>
    private sealed class QueryExplainFunctionInvocationFilter(ITestOutputHelper output) : IAutoFunctionInvocationFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Invoke the model to explain why the functions are being called 
            var message = context.ChatHistory[^2];
            var functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last());
            var functionNames = functionCalls.Select(fc => $"{fc.PluginName}-{fc.FunctionName}").ToList();
            var service = context.Kernel.GetRequiredService<IChatCompletionService>();

            var chatHistory = new ChatHistory
            {
                new ChatMessageContent(AuthorRole.User, $"Provide an explanation why these functions: {string.Join(',', functionNames)} need to be called to answer this query: {message.Content}")
            };
            var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };
            var result = await service.GetChatMessageContentAsync(chatHistory, executionSettings, context.Kernel);
            this._output.WriteLine(result);

            // Invoke the functions
            await next(context);
        }
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => $"12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy\nLocation: {location}";
    }

    private sealed class DecoratedWeatherPlugin
    {
        private readonly WeatherPlugin _weatherPlugin = new();

        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("A detailed explanation why this function is being called")] string explanation,
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => this._weatherPlugin.GetWeather(location);
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
