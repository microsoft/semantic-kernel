// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

public static class Example76_Filters
{
    private sealed class FirstFunctionFilter : IFunctionFilter
    {
        public void OnFunctionInvoking(FunctionInvokingContext context) =>
            Console.WriteLine($"{nameof(FirstFunctionFilter)}.{nameof(OnFunctionInvoking)} - {context.Function.Name}");

        public void OnFunctionInvoked(FunctionInvokedContext context) =>
            Console.WriteLine($"{nameof(FirstFunctionFilter)}.{nameof(OnFunctionInvoked)} - {context.Function.Name}");
    }

    private sealed class SecondFunctionFilter : IFunctionFilter
    {
        public void OnFunctionInvoking(FunctionInvokingContext context) =>
            Console.WriteLine($"{nameof(SecondFunctionFilter)}.{nameof(OnFunctionInvoking)} - {context.Function.Name}");

        public void OnFunctionInvoked(FunctionInvokedContext context) =>
            Console.WriteLine($"{nameof(SecondFunctionFilter)}.{nameof(OnFunctionInvoked)} - {context.Function.Name}");
    }

    private sealed class FirstPromptFilter : IPromptFilter
    {
        public void OnPromptRendering(PromptRenderingContext context) =>
            Console.WriteLine($"{nameof(FirstPromptFilter)}.{nameof(OnPromptRendering)} - {context.Function.Name}");

        public void OnPromptRendered(PromptRenderedContext context) =>
            Console.WriteLine($"{nameof(FirstPromptFilter)}.{nameof(OnPromptRendered)} - {context.Function.Name}");
    }

    public static async Task RunAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IFunctionFilter, FirstFunctionFilter>();
        builder.Services.AddSingleton<IFunctionFilter, SecondFunctionFilter>();
        builder.Services.AddSingleton<IPromptFilter, FirstPromptFilter>();

        var kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("What is Seattle", functionName: "MyFunction");
        var result = await kernel.InvokeAsync(function);

        Console.WriteLine();
        Console.WriteLine(result);

        Console.ReadKey();
    }

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
