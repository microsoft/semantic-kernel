// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example76_Filters : BaseTest
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
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", functions: new[] { function }));
        var result = await kernel.InvokeAsync(kernel.Plugins["MyPlugin"]["MyFunction"]);

        WriteLine(result);
    }

    public Example76_Filters(ITestOutputHelper output) : base(output)
    {
    }

    #region Filters

    private sealed class FirstFunctionFilter : IFunctionFilter
    {
        private readonly ITestOutputHelper _output;

        public FirstFunctionFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.FunctionInvoking - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.FunctionInvoked - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    private sealed class SecondFunctionFilter : IFunctionFilter
    {
        private readonly ITestOutputHelper _output;

        public SecondFunctionFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.FunctionInvoking - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.FunctionInvoked - {context.Function.PluginName}.{context.Function.Name}");
        }
    }

    private sealed class FirstPromptFilter : IPromptFilter
    {
        private readonly ITestOutputHelper _output;

        public FirstPromptFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        public void OnPromptRendering(PromptRenderingContext context) =>
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.{nameof(OnPromptRendering)} - {context.Function.PluginName}.{context.Function.Name}");

        public void OnPromptRendered(PromptRenderedContext context) =>
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.{nameof(OnPromptRendered)} - {context.Function.PluginName}.{context.Function.Name}");
    }

    #endregion

    #region Filter capabilities

    private sealed class FunctionFilterExample : IFunctionFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Example: override kernel arguments
            context.Arguments["input"] = "new input";

            // Without calling next(context), next filters in pipeline and actual function won't be invoked.
            await next(context);

            // Example: get function result value
            var value = context.Result!.GetValue<object>();

            // Example: get token usage from metadata
            var usage = context.Result.Metadata?["Usage"];

            // Example: override function result value
            context.Result = new FunctionResult(context.Function, "new result value");
        }
    }

    private sealed class ExceptionHandlingFilterExample : IFunctionFilter
    {
        private readonly ILogger _logger;

        public ExceptionHandlingFilterExample(ILogger logger)
        {
            this._logger = logger;
        }

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
                context.Result = new FunctionResult(context.Function, "Friendly message instead of exception");

                // Example: Rethrow another type of exception if needed
                throw new InvalidOperationException("New exception");
            }
        }
    }

    private sealed class PromptFilterExample : IPromptFilter
    {
        public void OnPromptRendered(PromptRenderedContext context)
        {
            // Example: override rendered prompt before sending it to AI
            context.RenderedPrompt = "Safe prompt";
        }

        public void OnPromptRendering(PromptRenderingContext context)
        {
            // Example: get function information
            var functionName = context.Function.Name;
        }
    }

    #endregion
}
