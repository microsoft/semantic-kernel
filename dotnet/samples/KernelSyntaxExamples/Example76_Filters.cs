// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
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

        public Task OnFunctionInvokingAsync(FunctionInvokingContext context)
        {
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.{nameof(OnFunctionInvokingAsync)} - {context.Function.PluginName}.{context.Function.Name}");
            return Task.CompletedTask;
        }

        public Task OnFunctionInvokedAsync(FunctionInvokedContext context)
        {
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.{nameof(OnFunctionInvokedAsync)} - {context.Function.PluginName}.{context.Function.Name}");
            return Task.CompletedTask;
        }
    }

    private sealed class SecondFunctionFilter : IFunctionFilter
    {
        private readonly ITestOutputHelper _output;

        public SecondFunctionFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        public Task OnFunctionInvokingAsync(FunctionInvokingContext context)
        {
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.{nameof(OnFunctionInvokingAsync)} - {context.Function.PluginName}.{context.Function.Name}");
            return Task.CompletedTask;
        }

        public Task OnFunctionInvokedAsync(FunctionInvokedContext context)
        {
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.{nameof(OnFunctionInvokedAsync)} - {context.Function.PluginName}.{context.Function.Name}");
            return Task.CompletedTask;
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
        public async Task OnFunctionInvokedAsync(FunctionInvokedContext context)
        {
            // Example: get function result value
            var value = context.Result.GetValue<object>();

            // Example: override function result value
            context.SetResultValue("new result value");

            // Example: get token usage from metadata
            var usage = context.Result.Metadata?["Usage"];

            // Example: check for exception during function execution
            // If it's not null, then some exception occurred
            if (context.Exception is not null)
            {
                // Possible options to handle it:

                // 1. Do not throw an exception that occurred during function execution
                context.Exception = null;

                // 2. Override the result with some value, that is meaningful to LLM
                context.SetResultValue("Friendly message instead of exception");

                // 3. Rethrow another type of exception if needed - Option 1.
                context.Exception = new Exception("New exception");

                // 3. Rethrow another type of exception if needed - Option 2.
                throw new Exception("New exception");
            }

            // Example: call asynchronous operations
            await AsyncOperation();
        }

        public async Task OnFunctionInvokingAsync(FunctionInvokingContext context)
        {
            // Example: override kernel arguments
            context.Arguments["input"] = "new input";

            // Example: cancel function execution
            context.Cancel = true;

            // Example: call asynchronous operations
            await AsyncOperation();
        }

        private Task AsyncOperation() => Task.CompletedTask;
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
