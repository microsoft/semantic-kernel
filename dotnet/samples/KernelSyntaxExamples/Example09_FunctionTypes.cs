// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using RepoUtils;

public static class Example09_FunctionTypes
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Method Function types ========");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        var plugin = kernel.ImportPluginFromType<LocalExamplePlugin>("Examples");

        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));

        // Using Kernel.InvokeAsync you can use the plugin reference or the kernel.Plugins collection

        await kernel.InvokeAsync(plugin["NoInputWithVoidResult"]);
        await kernel.InvokeAsync(kernel.Plugins["Examples"]["NoInputWithVoidResult"]);

        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputWithVoidResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputTaskWithVoidResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.InputDateTimeWithStringResult)], new() { ["currentDate"] = DateTime.Now });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputTaskWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.MultipleInputsWithVoidResult)], new() { ["x"] = "x string", ["y"] = 100, ["z"] = 1.5 });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.ComplexInputWithStringResult)], new() { ["complexObject"] = new LocalExamplePlugin() });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.InputStringTaskWithStringResult)], new() { ["echoInput"] = "return this" });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.InputStringTaskWithVoidResult)], new() { ["x"] = "x input" });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputWithFunctionResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputTaskWithFunctionResult)]);

        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingKernelWithInputTextAndStringResult)],
            new()
            {
                ["textToSummarize"] = @"C# is a modern, versatile language by Microsoft, blending the efficiency of C++ 
                                            with Visual Basic's simplicity. It's ideal for a wide range of applications, 
                                            emphasizing type safety, modularity, and modern programming paradigms."
            });
    }
}
// Task functions when are imported as plugins loose the "Async" suffix if present.
#pragma warning disable IDE1006 // Naming Styles

public class LocalExamplePlugin
{
    /// <summary>
    /// Example of using a void function with no input
    /// </summary>
    [KernelFunction]
    public void NoInputWithVoidResult()
    {
        Console.WriteLine($"Running {nameof(this.NoInputWithVoidResult)} -> No input");
    }

    /// <summary>
    /// Example of using a void task function with no input
    /// </summary>
    [KernelFunction]
    public Task NoInputTaskWithVoidResult()
    {
        Console.WriteLine($"Running {nameof(this.NoInputTaskWithVoidResult)} -> No input");
        return Task.CompletedTask;
    }

    /// <summary>
    /// Example of using a function with a DateTime input and a string result
    /// </summary>
    [KernelFunction]
    public string InputDateTimeWithStringResult(DateTime currentDate)
    {
        var result = currentDate.ToString(CultureInfo.InvariantCulture);
        Console.WriteLine($"Running {nameof(this.InputDateTimeWithStringResult)} -> [currentDate = {currentDate}] -> result: {result}");
        return result;
    }

    /// <summary>
    /// Example of using a Task function with no input and a string result
    /// </summary>
    [KernelFunction]
    public Task<string> NoInputTaskWithStringResult()
    {
        var result = "string result";
        Console.WriteLine($"Running {nameof(this.NoInputTaskWithStringResult)} -> No input -> result: {result}");
        return Task.FromResult(result);
    }

    /// <summary>
    /// Example how to inject Kernel in your function
    /// This example uses the injected kernel to invoke a plugin from within another function
    /// </summary>
    [KernelFunction]
    public async Task<string> TaskInjectingKernelWithInputTextAndStringResult(Kernel kernel, string textToSummarize)
    {
        var summary = await kernel.InvokeAsync<string>(kernel.Plugins["SummarizePlugin"]["Summarize"], new() { ["input"] = textToSummarize });
        Console.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected kernel + input: [textToSummarize: {textToSummarize[..15]}...{textToSummarize[^15..]}] -> result: {summary}");
        return summary!;
    }

    /// <summary>
    /// Example passing multiple parameters with multiple types
    /// </summary>
    [KernelFunction]
    public void MultipleInputsWithVoidResult(string x, int y, double z)
    {
        Console.WriteLine($"Running {nameof(this.MultipleInputsWithVoidResult)} -> input: [x = {x}, y = {y}, z = {z}]");
    }

    /// <summary>
    /// Example passing a complex object and returning a string result
    /// </summary>
    [KernelFunction]
    public string ComplexInputWithStringResult(object complexObject)
    {
        var result = complexObject.GetType().Name;
        Console.WriteLine($"Running {nameof(this.ComplexInputWithStringResult)} -> input: [complexObject = {complexObject}] -> result: {result}");
        return result;
    }

    /// <summary>
    /// Example using an async task function echoing the input
    /// </summary>
    [KernelFunction]
    public Task<string> InputStringTaskWithStringResult(string echoInput)
    {
        Console.WriteLine($"Running {nameof(this.InputStringTaskWithStringResult)} -> input: [echoInput = {echoInput}] -> result: {echoInput}");
        return Task.FromResult(echoInput);
    }

    /// <summary>
    /// Example using an async void task with string input
    /// </summary>
    [KernelFunction]
    public Task InputStringTaskWithVoidResult(string x)
    {
        Console.WriteLine($"Running {nameof(this.InputStringTaskWithVoidResult)} -> input: [x = {x}]");
        return Task.CompletedTask;
    }

    /// <summary>
    /// Example using a function to return the result of another inner function
    /// </summary>
    [KernelFunction]
    public FunctionResult NoInputWithFunctionResult()
    {
        var myInternalFunction = KernelFunctionFactory.CreateFromMethod(() => { });
        var result = new FunctionResult(myInternalFunction);
        Console.WriteLine($"Running {nameof(this.NoInputWithFunctionResult)} -> No input -> result: {result.GetType().Name}");
        return result;
    }

    /// <summary>
    /// Example using a task function to return the result of another kernel function
    /// </summary>
    [KernelFunction]
    public async Task<FunctionResult> NoInputTaskWithFunctionResult(Kernel kernel)
    {
        var result = await kernel.InvokeAsync(kernel.Plugins["Examples"]["NoInputWithVoidResult"]);
        Console.WriteLine($"Running {nameof(this.NoInputTaskWithFunctionResult)} -> Injected kernel -> result: {result.GetType().Name}");
        return result;
    }

    public override string ToString()
    {
        return "Complex type result ToString override";
    }
}
#pragma warning restore IDE1006 // Naming Styles
