// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example76_Filters(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to use function and prompt filters in Kernel.
    /// </summary>
    [Fact]
    public async Task FunctionAndPromptFiltersAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<ITestOutputHelper>(this.Output);

        // Add filters with DI
        builder.Services.AddSingleton<IFunctionFilter, FirstFunctionFilter>();
        builder.Services.AddSingleton<IFunctionFilter, SecondFunctionFilter>();

        var kernel = builder.Build();

        // Add filter without DI
        kernel.PromptFilters.Add(new FirstPromptFilter(this.Output));

        var function = kernel.CreateFunctionFromPrompt("What is Seattle", functionName: "MyFunction");
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", functions: [function]));
        var result = await kernel.InvokeAsync(kernel.Plugins["MyPlugin"]["MyFunction"]);

        WriteLine(result);
    }

    [Fact]
    public async Task FunctionFilterResultOverrideAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter overrides result with "Result from filter" value.
        builder.Services.AddSingleton<IFunctionFilter, FunctionFilterExample>();

        var kernel = builder.Build();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result from method");

        var result = await kernel.InvokeAsync(function);

        WriteLine(result);
        WriteLine($"Metadata: {string.Join(",", result.Metadata!.Select(kv => $"{kv.Key}: {kv.Value}"))}");

        // Output:
        // Result from filter.
        // Metadata: metadata_key: metadata_value
    }

    [Fact]
    public async Task FunctionFilterResultOverrideOnStreamingAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter overrides streaming results with "item * 2" logic.
        builder.Services.AddSingleton<IFunctionFilter, StreamingFunctionFilterExample>();

        var kernel = builder.Build();

        static async IAsyncEnumerable<int> GetData()
        {
            yield return 1;
            yield return 2;
            yield return 3;
        }

        var function = KernelFunctionFactory.CreateFromMethod(GetData);

        await foreach (var item in kernel.InvokeStreamingAsync<int>(function))
        {
            WriteLine(item);
        }

        // Output: 2, 4, 6.
    }

    [Fact]
    public async Task FunctionFilterExceptionHandlingAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter handles an exception and returns overridden result.
        builder.Services.AddSingleton<IFunctionFilter>(new ExceptionHandlingFilterExample(NullLogger.Instance));

        var kernel = builder.Build();

        // Simulation of exception during function invocation.
        var function = KernelFunctionFactory.CreateFromMethod(() => { throw new KernelException("Exception in function"); });

        var result = await kernel.InvokeAsync(function);

        WriteLine(result);

        // Output: Friendly message instead of exception.
    }

    [Fact]
    public async Task FunctionFilterExceptionHandlingOnStreamingAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter handles an exception and returns overridden streaming result.
        builder.Services.AddSingleton<IFunctionFilter>(new StreamingExceptionHandlingFilterExample(NullLogger.Instance));

        var kernel = builder.Build();

        static async IAsyncEnumerable<string> GetData()
        {
            yield return "first chunk";
            // Simulation of exception during function invocation.
            throw new KernelException("Exception in function");
        }

        var function = KernelFunctionFactory.CreateFromMethod(GetData);

        await foreach (var item in kernel.InvokeStreamingAsync<string>(function))
        {
            WriteLine(item);
        }

        // Output: first chunk, chunk instead of exception.
    }

    [Fact]
    public async Task FunctionCallFilterAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey);

        // This filter handles an exception and returns overridden result.
        builder.Services.AddSingleton<IFunctionCallFilter>(new FunctionCallFilter(this.Output));

        var kernel = builder.Build();

        var function = KernelFunctionFactory.CreateFromMethod(() => "Result from function", "MyFunction");

        kernel.ImportPluginFromFunctions("MyPlugin", [function]);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.RequireFunction(function.Metadata.ToOpenAIFunction(), autoInvoke: true)
        };

        var result = await kernel.InvokePromptAsync("Invoke provided function", new(executionSettings));

        WriteLine(result);

        // Output:
        // Function call iteration: 1 out of 1
        // Request iteration: 1
        // Result from function call filter
    }

    #region Filter capabilities

    /// <summary>Shows syntax for function filter in non-streaming scenario.</summary>
    private sealed class FunctionFilterExample : IFunctionFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Example: override kernel arguments
            context.Arguments["input"] = "new input";

            // This call is required to proceed with next filters in pipeline and actual function.
            // Without this call next filters and function won't be invoked.
            await next(context);

            // Example: get function result value
            var value = context.Result!.GetValue<object>();

            // Example: get token usage from metadata
            var usage = context.Result.Metadata?["Usage"];

            // Example: override function result value and metadata
            Dictionary<string, object?> metadata = context.Result.Metadata is not null ? new(context.Result.Metadata) : [];
            metadata["metadata_key"] = "metadata_value";

            context.Result = new FunctionResult(context.Result, "Result from filter")
            {
                Metadata = metadata
            };
        }
    }

    /// <summary>Shows syntax for prompt filter.</summary>
    private sealed class PromptFilterExample : IPromptFilter
    {
        public async Task OnPromptRenderingAsync(PromptRenderingContext context, Func<PromptRenderingContext, Task> next)
        {
            // Example: get function information
            var functionName = context.Function.Name;

            await next(context);

            // Example: override rendered prompt before sending it to AI
            context.RenderedPrompt = "Safe prompt";
        }
    }

    /// <summary>Shows syntax for function call filter.</summary>
    private sealed class FunctionCallFilter(ITestOutputHelper output) : IFunctionCallFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnFunctionCallInvocationAsync(FunctionCallInvocationContext context, Func<FunctionCallInvocationContext, Task> next)
        {
            // Example: get function information
            var functionName = context.Function.Name;

            // Example: get function call iteration information
            this._output.WriteLine($"Function call iteration: {context.FunctionCallIteration + 1} out of {context.FunctionCallCount}");

            // Example: get request iteration
            this._output.WriteLine($"Request iteration: {context.RequestIteration + 1}");

            // Calling next filter in pipeline or function itself.
            // By skipping this call, next filters and function won't be invoked, and function call loop will proceed to the next function.
            await next(context);

            // Example: get function result
            var result = context.Result;

            // Example: override function result value
            context.Result = new FunctionResult(context.Result, "Result from function call filter");

            // Example: stop further function calling. but proceed with request iteration
            context.Action = FunctionCallAction.StopFunctionCallIteration;

            // Example: call remaining functions, but stop request iteration
            context.Action = FunctionCallAction.StopRequestIteration;

            // Example: stop function calling and request iterations, return immediately
            context.Action = FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration;
        }
    }

    /// <summary>Shows syntax for function filter in streaming scenario.</summary>
    private sealed class StreamingFunctionFilterExample : IFunctionFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            await next(context);

            // In streaming scenario, async enumerable is available in context result object.
            // To override data: get async enumerable from function result, override data and set new async enumerable in context result:
            var enumerable = context.Result.GetValue<IAsyncEnumerable<int>>();
            context.Result = new FunctionResult(context.Result, OverrideStreamingDataAsync(enumerable!));
        }

        private async IAsyncEnumerable<int> OverrideStreamingDataAsync(IAsyncEnumerable<int> data)
        {
            await foreach (var item in data)
            {
                // Example: override streaming data
                yield return item * 2;
            }
        }
    }

    /// <summary>Shows syntax for exception handling in function filter in non-streaming scenario.</summary>
    private sealed class ExceptionHandlingFilterExample(ILogger logger) : IFunctionFilter
    {
        private readonly ILogger _logger = logger;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            try
            {
                await next(context);
            }
            catch (Exception exception)
            {
                this._logger.LogError(exception, "Something went wrong during function invocation");

                // Example: override function result value
                context.Result = new FunctionResult(context.Result, "Friendly message instead of exception");

                // Example: Rethrow another type of exception if needed
                // throw new InvalidOperationException("New exception");
            }
        }
    }

    /// <summary>Shows syntax for exception handling in function filter in streaming scenario.</summary>
    private sealed class StreamingExceptionHandlingFilterExample(ILogger logger) : IFunctionFilter
    {
        private readonly ILogger _logger = logger;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            await next(context);

            var enumerable = context.Result.GetValue<IAsyncEnumerable<string>>();
            context.Result = new FunctionResult(context.Result, StreamingWithExceptionHandlingAsync(enumerable!));
        }

        private async IAsyncEnumerable<string> StreamingWithExceptionHandlingAsync(IAsyncEnumerable<string> data)
        {
            var enumerator = data.GetAsyncEnumerator();

            await using (enumerator.ConfigureAwait(false))
            {
                while (true)
                {
                    string result;

                    try
                    {
                        if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                        {
                            break;
                        }

                        result = enumerator.Current;
                    }
                    catch (Exception exception)
                    {
                        this._logger.LogError(exception, "Something went wrong during function invocation");

                        result = "chunk instead of exception";
                    }

                    yield return result;
                }
            }
        }
    }

    #endregion

    #region Filters

    private sealed class FirstFunctionFilter(ITestOutputHelper output) : IFunctionFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.FunctionInvoking - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.FunctionInvoked - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    private sealed class SecondFunctionFilter(ITestOutputHelper output) : IFunctionFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.FunctionInvoking - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.FunctionInvoked - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    private sealed class FirstPromptFilter(ITestOutputHelper output) : IPromptFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnPromptRenderingAsync(PromptRenderingContext context, Func<PromptRenderingContext, Task> next)
        {
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.PromptRendering - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.PromptRendered - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    #endregion
}
