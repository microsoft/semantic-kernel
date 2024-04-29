// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Filtering;

public class AutoFunctionInvocationFiltering(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task AutoFunctionInvocationFilterAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey);

        // This filter outputs information about auto function invocation and returns overridden result.
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoFunctionInvocationFilterExample(this.Output));

        var kernel = builder.Build();

        var function = KernelFunctionFactory.CreateFromMethod(() => "Result from function", "MyFunction");

        kernel.ImportPluginFromFunctions("MyPlugin", [function]);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.RequireFunction(function.Metadata.ToOpenAIFunction(), autoInvoke: true)
        };

        var result = await kernel.InvokePromptAsync("Invoke provided function and return result", new(executionSettings));

        WriteLine(result);

        // Output:
        // Request sequence number: 0
        // Function sequence number: 0
        // Total number of functions: 1
        // Result from auto function invocation filter.
    }

    /// <summary>Shows syntax for auto function invocation filter.</summary>
    private sealed class AutoFunctionInvocationFilterExample(ITestOutputHelper output) : IAutoFunctionInvocationFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Example: get function information
            var functionName = context.Function.Name;

            // Example: get chat history
            var chatHistory = context.ChatHistory;

            // Example: get information about all functions which will be invoked
            var functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last());

            // Example: get request sequence index
            this._output.WriteLine($"Request sequence index: {context.RequestSequenceIndex}");

            // Example: get function sequence index
            this._output.WriteLine($"Function sequence index: {context.FunctionSequenceIndex}");

            // Example: get total number of functions which will be called
            this._output.WriteLine($"Total number of functions: {context.FunctionCount}");

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
}
