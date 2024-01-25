// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Examples;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

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
        var result = await kernel.InvokeAsync(function);

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

        public void OnFunctionInvoking(FunctionInvokingContext context) =>
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.{nameof(OnFunctionInvoking)} - {context.Function.Name}");

        public void OnFunctionInvoked(FunctionInvokedContext context) =>
            this._output.WriteLine($"{nameof(FirstFunctionFilter)}.{nameof(OnFunctionInvoked)} - {context.Function.Name}");
    }

    private sealed class SecondFunctionFilter : IFunctionFilter
    {
        private readonly ITestOutputHelper _output;

        public SecondFunctionFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        public void OnFunctionInvoking(FunctionInvokingContext context) =>
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.{nameof(OnFunctionInvoking)} - {context.Function.Name}");

        public void OnFunctionInvoked(FunctionInvokedContext context) =>
            this._output.WriteLine($"{nameof(SecondFunctionFilter)}.{nameof(OnFunctionInvoked)} - {context.Function.Name}");
    }

    private sealed class FirstPromptFilter : IPromptFilter
    {
        private readonly ITestOutputHelper _output;

        public FirstPromptFilter(ITestOutputHelper output)
        {
            this._output = output;
        }

        public void OnPromptRendering(PromptRenderingContext context) =>
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.{nameof(OnPromptRendering)} - {context.Function.Name}");

        public void OnPromptRendered(PromptRenderedContext context) =>
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.{nameof(OnPromptRendered)} - {context.Function.Name}");
    }

    #endregion

    #region Filter capabilities

    private sealed class FunctionFilterExample : IFunctionFilter
    {
        public void OnFunctionInvoked(FunctionInvokedContext context)
        {
            // Example: get function result value
            var value = context.Result.GetValue<object>();

            // Example: override function result value
            context.SetResultValue("new result value");

            // Example: get token usage from metadata
            var usage = context.Result.Metadata?["Usage"];
        }

        public void OnFunctionInvoking(FunctionInvokingContext context)
        {
            // Example: override kernel arguments
            context.Arguments["input"] = "new input";

            // Example: cancel function execution
            context.Cancel = true;
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
