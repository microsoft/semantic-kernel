// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;

namespace Filtering;

public class FunctionInvocationFiltering(ITestOutputHelper output) : BaseTest(output)
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
        builder.Services.AddSingleton<IFunctionInvocationFilter, FirstFunctionFilter>();
        builder.Services.AddSingleton<IFunctionInvocationFilter, SecondFunctionFilter>();

        var kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("What is Seattle", functionName: "MyFunction");
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", functions: [function]));
        var result = await kernel.InvokeAsync(kernel.Plugins["MyPlugin"]["MyFunction"]);

        Console.WriteLine(result);
    }

    [Fact]
    public async Task FunctionFilterResultOverrideAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter overrides result with "Result from filter" value.
        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionFilterExample>();

        var kernel = builder.Build();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result from method");

        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result);
        Console.WriteLine($"Metadata: {string.Join(",", result.Metadata!.Select(kv => $"{kv.Key}: {kv.Value}"))}");

        // Output:
        // Result from filter.
        // Metadata: metadata_key: metadata_value
    }

    [Fact]
    public async Task FunctionFilterResultOverrideOnStreamingAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter overrides streaming results with "item * 2" logic.
        builder.Services.AddSingleton<IFunctionInvocationFilter, StreamingFunctionFilterExample>();

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
            Console.WriteLine(item);
        }

        // Output: 2, 4, 6.
    }

    [Fact]
    public async Task FunctionFilterExceptionHandlingAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter handles an exception and returns overridden result.
        builder.Services.AddSingleton<IFunctionInvocationFilter>(new ExceptionHandlingFilterExample(NullLogger.Instance));

        var kernel = builder.Build();

        // Simulation of exception during function invocation.
        var function = KernelFunctionFactory.CreateFromMethod(() => { throw new KernelException("Exception in function"); });

        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result);

        // Output: Friendly message instead of exception.
    }

    [Fact]
    public async Task FunctionFilterExceptionHandlingOnStreamingAsync()
    {
        var builder = Kernel.CreateBuilder();

        // This filter handles an exception and returns overridden streaming result.
        builder.Services.AddSingleton<IFunctionInvocationFilter>(new StreamingExceptionHandlingFilterExample(NullLogger.Instance));

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
            Console.WriteLine(item);
        }

        // Output: first chunk, chunk instead of exception.
    }

    #region Filter capabilities

    /// <summary>Shows syntax for function filter in non-streaming scenario.</summary>
    private sealed class FunctionFilterExample : IFunctionInvocationFilter
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

    /// <summary>Shows syntax for function filter in streaming scenario.</summary>
    private sealed class StreamingFunctionFilterExample : IFunctionInvocationFilter
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
    private sealed class ExceptionHandlingFilterExample(ILogger logger) : IFunctionInvocationFilter
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
    private sealed class StreamingExceptionHandlingFilterExample(ILogger logger) : IFunctionInvocationFilter
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

    private sealed class FirstFunctionFilter(ITestOutputHelper output) : IFunctionInvocationFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.FunctionInvoking - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.FunctionInvoked - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    private sealed class SecondFunctionFilter(ITestOutputHelper output) : IFunctionInvocationFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.FunctionInvoking - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.FunctionInvoked - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    #endregion
}
