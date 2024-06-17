// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Filtering;

public class AutoFunctionInvocationFiltering(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to use <see cref="IAutoFunctionInvocationFilter"/> in non-streaming scenario.
    /// </summary>
    [Fact]
    public async Task AutoFunctionInvocationFilterNonStreamingAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey);

        // This filter outputs information about auto function invocation and returns overridden result.
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoFunctionInvocationNonStreamingFilter(this.Output));

        var kernel = builder.Build();

        var function = KernelFunctionFactory.CreateFromMethod(() => "Result from function", "MyFunction");

        kernel.ImportPluginFromFunctions("MyPlugin", [function]);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.RequireFunction(function.Metadata.ToOpenAIFunction(), autoInvoke: true)
        };

        var result = await kernel.InvokePromptAsync("Invoke provided function and return result", new(executionSettings));

        Console.WriteLine(result);

        // Output:
        // Request sequence number: 0
        // Function sequence number: 0
        // Total number of functions: 1
        // Result from auto function invocation filter.
    }

    /// <summary>
    /// Shows how to use <see cref="IAutoFunctionInvocationFilter"/> in streaming scenario.
    /// </summary>
    [Fact]
    public async Task AutoFunctionInvocationFilterStreamingAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion("gpt-3.5-turbo-1106", TestConfiguration.OpenAI.ApiKey);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoFunctionInvocationStreamingFilter(this.Output));

        var kernel = builder.Build();

        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    "London" => "55 and cloudy",
                    "Miami" => "80 and sunny",
                    "Paris" => "60 and rainy",
                    "Tokyo" => "50 and sunny",
                    "Sydney" => "75 and sunny",
                    "Tel Aviv" => "80 and sunny",
                    _ => "31 and snowing",
                }, "GetWeatherForCity", "Gets the current weather for the specified city"),
        ]);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        await foreach (var chunk in kernel.InvokePromptStreamingAsync("Check current UTC time and return current weather in Boston city.", new(executionSettings)))
        {
            Console.WriteLine(chunk.ToString());
        }

        // Output:
        // Request #0. Function call: HelperFunctions.GetCurrentUtcTime.
        // Request #0. Function call: HelperFunctions.GetWeatherForCity.
        // The current UTC time is {time of execution}, and the current weather in Boston is 61°F and rainy.
    }

    /// <summary>Shows syntax for auto function invocation filter.</summary>
    private sealed class AutoFunctionInvocationNonStreamingFilter(ITestOutputHelper output) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Example: get function information
            var functionName = context.Function.Name;

            // Example: get chat history
            var chatHistory = context.ChatHistory;

            // Example: get information about all functions which will be invoked
            var functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last());

            // Example: get request sequence index
            output.WriteLine($"Request sequence index: {context.RequestSequenceIndex}");

            // Example: get function sequence index
            output.WriteLine($"Function sequence index: {context.FunctionSequenceIndex}");

            // Example: get total number of functions which will be called
            output.WriteLine($"Total number of functions: {context.FunctionCount}");

            // Calling next filter in pipeline or function itself.
            // By skipping this call, next filters and function won't be invoked, and function call loop will proceed to the next function.
            await next(context);

            // Example: get function result
            var result = context.Result;

            // Example: override function result value
            context.Result = new FunctionResult(context.Result, "Result from auto function invocation filter");

            // Example: Terminate function invocation
            context.Terminate = true;
        }
    }

    /// <summary>Shows syntax for auto function invocation filter for streaming scenario.</summary>
    private sealed class AutoFunctionInvocationStreamingFilter(ITestOutputHelper output) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            var chatHistory = context.ChatHistory;

            var functionCalls = FunctionCallContent.GetFunctionCalls(chatHistory.Last()).ToArray();

            if (functionCalls is { Length: > 0 })
            {
                foreach (var functionCall in functionCalls)
                {
                    output.WriteLine($"Request #{context.RequestSequenceIndex}. Function call: {functionCall.PluginName}.{functionCall.FunctionName}.");
                }
            }

            await next(context);
        }
    }
}
