// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Functions;

public class MethodFunctions_Types(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Method Function types ========");

        var builder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
        builder.Services.AddLogging(services => services.AddConsole().SetMinimumLevel(LogLevel.Warning));
        builder.Services.AddSingleton(this.Output);
        var kernel = builder.Build();
        kernel.Culture = new CultureInfo("pt-BR");

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        var plugin = kernel.ImportPluginFromType<LocalExamplePlugin>("Examples");

        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));

        // Different ways to invoke a function (not limited to these examples)
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputWithVoidResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputTaskWithVoidResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.InputDateTimeWithStringResult)], new() { ["currentDate"] = DateTime.Now });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputTaskWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.MultipleInputsWithVoidResult)], new() { ["x"] = "x string", ["y"] = 100, ["z"] = 1.5 });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.ComplexInputWithStringResult)], new() { ["complexObject"] = new LocalExamplePlugin(this.Output) });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.InputStringTaskWithStringResult)], new() { ["echoInput"] = "return this" });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.InputStringTaskWithVoidResult)], new() { ["x"] = "x input" });
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputWithFunctionResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.NoInputTaskWithFunctionResult)]);

        // Injecting Parameters Examples
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingKernelFunctionWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingLoggerWithNoResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingLoggerFactoryWithNoResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingCultureInfoOrIFormatProviderWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingCancellationTokenWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingServiceSelectorWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingKernelWithInputTextAndStringResult)],
            new()
            {
                ["textToSummarize"] = @"C# is a modern, versatile language by Microsoft, blending the efficiency of C++
                                            with Visual Basic's simplicity. It's ideal for a wide range of applications,
                                            emphasizing type safety, modularity, and modern programming paradigms."
            });

        // You can also use the kernel.Plugins collection to invoke a function
        await kernel.InvokeAsync(kernel.Plugins["Examples"][nameof(LocalExamplePlugin.NoInputWithVoidResult)]);
    }
}
// Task functions when are imported as plugins loose the "Async" suffix if present.
#pragma warning disable IDE1006 // Naming Styles

public class LocalExamplePlugin(ITestOutputHelper output)
{
    private readonly ITestOutputHelper _output = output;

    /// <summary>
    /// Example of using a void function with no input
    /// </summary>
    [KernelFunction]
    public void NoInputWithVoidResult()
    {
        this._output.WriteLine($"Running {nameof(this.NoInputWithVoidResult)} -> No input");
    }

    /// <summary>
    /// Example of using a void task function with no input
    /// </summary>
    [KernelFunction]
    public Task NoInputTaskWithVoidResult()
    {
        this._output.WriteLine($"Running {nameof(this.NoInputTaskWithVoidResult)} -> No input");
        return Task.CompletedTask;
    }

    /// <summary>
    /// Example of using a function with a DateTime input and a string result
    /// </summary>
    [KernelFunction]
    public string InputDateTimeWithStringResult(DateTime currentDate)
    {
        var result = currentDate.ToString(CultureInfo.InvariantCulture);
        this._output.WriteLine($"Running {nameof(this.InputDateTimeWithStringResult)} -> [currentDate = {currentDate}] -> result: {result}");
        return result;
    }

    /// <summary>
    /// Example of using a Task function with no input and a string result
    /// </summary>
    [KernelFunction]
    public Task<string> NoInputTaskWithStringResult()
    {
        var result = "string result";
        this._output.WriteLine($"Running {nameof(this.NoInputTaskWithStringResult)} -> No input -> result: {result}");
        return Task.FromResult(result);
    }

    /// <summary>
    /// Example passing multiple parameters with multiple types
    /// </summary>
    [KernelFunction]
    public void MultipleInputsWithVoidResult(string x, int y, double z)
    {
        this._output.WriteLine($"Running {nameof(this.MultipleInputsWithVoidResult)} -> input: [x = {x}, y = {y}, z = {z}]");
    }

    /// <summary>
    /// Example passing a complex object and returning a string result
    /// </summary>
    [KernelFunction]
    public string ComplexInputWithStringResult(object complexObject)
    {
        var result = complexObject.GetType().Name;
        this._output.WriteLine($"Running {nameof(this.ComplexInputWithStringResult)} -> input: [complexObject = {complexObject}] -> result: {result}");
        return result;
    }

    /// <summary>
    /// Example using an async task function echoing the input
    /// </summary>
    [KernelFunction]
    public Task<string> InputStringTaskWithStringResult(string echoInput)
    {
        this._output.WriteLine($"Running {nameof(this.InputStringTaskWithStringResult)} -> input: [echoInput = {echoInput}] -> result: {echoInput}");
        return Task.FromResult(echoInput);
    }

    /// <summary>
    /// Example using an async void task with string input
    /// </summary>
    [KernelFunction]
    public Task InputStringTaskWithVoidResult(string x)
    {
        this._output.WriteLine($"Running {nameof(this.InputStringTaskWithVoidResult)} -> input: [x = {x}]");
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
        this._output.WriteLine($"Running {nameof(this.NoInputWithFunctionResult)} -> No input -> result: {result.GetType().Name}");
        return result;
    }

    /// <summary>
    /// Example using a task function to return the result of another kernel function
    /// </summary>
    [KernelFunction]
    public async Task<FunctionResult> NoInputTaskWithFunctionResult(Kernel kernel)
    {
        var result = await kernel.InvokeAsync(kernel.Plugins["Examples"][nameof(this.NoInputWithVoidResult)]);
        this._output.WriteLine($"Running {nameof(this.NoInputTaskWithFunctionResult)} -> Injected kernel -> result: {result.GetType().Name}");
        return result;
    }

    /// <summary>
    /// Example how to inject Kernel in your function
    /// This example uses the injected kernel to invoke a plugin from within another function
    /// </summary>
    [KernelFunction]
    public async Task<string> TaskInjectingKernelWithInputTextAndStringResult(Kernel kernel, string textToSummarize)
    {
        var summary = await kernel.InvokeAsync<string>(kernel.Plugins["SummarizePlugin"]["Summarize"], new() { ["input"] = textToSummarize });
        this._output.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected kernel + input: [textToSummarize: {textToSummarize[..15]}...{textToSummarize[^15..]}] -> result: {summary}");
        return summary!;
    }

    /// <summary>
    /// Example how to inject the executing KernelFunction as a parameter
    /// </summary>
    [KernelFunction, Description("Example function injecting itself as a parameter")]
    public async Task<string> TaskInjectingKernelFunctionWithStringResult(KernelFunction executingFunction)
    {
        var result = $"Name: {executingFunction.Name}, Description: {executingFunction.Description}";
        this._output.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Function -> result: {result}");
        return result;
    }

    /// <summary>
    /// Example how to inject ILogger in your function
    /// </summary>
    [KernelFunction]
    public Task TaskInjectingLoggerWithNoResult(ILogger logger)
    {
        logger.LogWarning("Running {FunctionName} -> Injected Logger", nameof(this.TaskInjectingLoggerWithNoResult));
        this._output.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Logger");
        return Task.CompletedTask;
    }

    /// <summary>
    /// Example how to inject ILoggerFactory in your function
    /// </summary>
    [KernelFunction]
    public Task TaskInjectingLoggerFactoryWithNoResult(ILoggerFactory loggerFactory)
    {
        loggerFactory
            .CreateLogger<LocalExamplePlugin>()
            .LogWarning("Running {FunctionName} -> Injected Logger", nameof(this.TaskInjectingLoggerWithNoResult));

        this._output.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Logger");
        return Task.CompletedTask;
    }

    /// <summary>
    /// Example how to inject a service selector in your function and use a specific service
    /// </summary>
    [KernelFunction]
    public async Task<string> TaskInjectingServiceSelectorWithStringResult(Kernel kernel, KernelFunction function, KernelArguments arguments, IAIServiceSelector serviceSelector)
    {
        ChatMessageContent? chatMessageContent = null;
        if (serviceSelector.TrySelectAIService<IChatCompletionService>(kernel, function, arguments, out var chatCompletion, out var executionSettings))
        {
            chatMessageContent = await chatCompletion.GetChatMessageContentAsync(new ChatHistory("How much is 5 + 5 ?"), executionSettings);
        }

        var result = chatMessageContent?.Content;
        this._output.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Kernel, KernelFunction, KernelArguments, Service Selector -> result: {result}");
        return result ?? string.Empty;
    }

    /// <summary>
    /// Example how to inject CultureInfo or IFormatProvider in your function
    /// </summary>
    [KernelFunction]
    public async Task<string> TaskInjectingCultureInfoOrIFormatProviderWithStringResult(CultureInfo cultureInfo, IFormatProvider formatProvider)
    {
        var result = $"Culture Name: {cultureInfo.Name}, FormatProvider Equals CultureInfo?: {formatProvider.Equals(cultureInfo)}";
        this._output.WriteLine($"Running {nameof(this.TaskInjectingCultureInfoOrIFormatProviderWithStringResult)} -> Injected CultureInfo, IFormatProvider -> result: {result}");
        return result;
    }

    /// <summary>
    /// Example how to inject current CancellationToken in your function
    /// </summary>
    [KernelFunction]
    public async Task<string> TaskInjectingCancellationTokenWithStringResult(CancellationToken cancellationToken)
    {
        var result = $"Cancellation resquested: {cancellationToken.IsCancellationRequested}";
        this._output.WriteLine($"Running {nameof(this.TaskInjectingCultureInfoOrIFormatProviderWithStringResult)} -> Injected Cancellation Token -> result: {result}");
        return result;
    }

    public override string ToString()
    {
        return "Complex type result ToString override";
    }
}
#pragma warning restore IDE1006 // Naming Styles
