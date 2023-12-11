// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example57_KernelHooks
{
    private static string? s_openAIModelId;
    private static string? s_openAIApiKey;

    public static async Task RunAsync()
    {
        Console.WriteLine("\n======== Using Function Execution Handlers ========\n");

        s_openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        s_openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (s_openAIModelId == null || s_openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        await GetUsageAsync();

        await GetRenderedPromptAsync();

        await ChangingResultAsync();

        await BeforeInvokeCancellationAsync();

        await AfterInvokeCancellationAsync();
    }

    /// <summary>
    /// Demonstrate using kernel invocation-hooks to monitor usage:
    /// <see cref="Kernel.FunctionInvoking"/>
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static async Task GetUsageAsync()
    {
        Console.WriteLine("\n======== Get Usage Data ========\n");

        // Create kernel instance
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: s_openAIModelId!,
                apiKey: s_openAIApiKey!)
            .Build();

        // Initialize prompt
        const string FunctionPrompt = "Write a random paragraph about: {{$input}}.";

        var excuseFunction = kernel.CreateFunctionFromPrompt(
            FunctionPrompt,
            functionName: "Excuse",
            executionSettings: new OpenAIPromptExecutionSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        // Define hooks
        void MyPreHandler(object? sender, FunctionInvokingEventArgs e)
        {
            Console.WriteLine($"{e.Function.Name} : Pre Execution Handler - Triggered");
        }

        void MyRemovedPreExecutionHandler(object? sender, FunctionInvokingEventArgs e)
        {
            Console.WriteLine($"{e.Function.Name} : Pre Execution Handler - Should not trigger");
            e.Cancel = true;
        }

        void MyPostExecutionHandler(object? sender, FunctionInvokedEventArgs e)
        {
            Console.WriteLine($"{e.Function.Name} : Post Execution Handler - Usage: {e.Result.Metadata?["Usage"]?.AsJson()}");
        }

        kernel.FunctionInvoking += MyPreHandler;
        kernel.FunctionInvoked += MyPostExecutionHandler;

        // Demonstrate pattern for removing a handler.
        // Note: MyRemovedPreExecutionHandler will cancel execution if not removed.
        kernel.FunctionInvoking += MyRemovedPreExecutionHandler;
        kernel.FunctionInvoking -= MyRemovedPreExecutionHandler;

        // Invoke prompt to trigger execution hooks.
        const string Input = "I missed the F1 final race";
        var result = await kernel.InvokeAsync(excuseFunction, new() { ["input"] = Input });
        Console.WriteLine($"Function Result: {result}");
    }

    /// <summary>
    /// Demonstrate using kernel-hooks to around prompt rendering:
    /// <see cref="Kernel.PromptRendering"/>
    /// <see cref="Kernel.PromptRendered"/>
    /// </summary>
    private static async Task GetRenderedPromptAsync()
    {
        Console.WriteLine("\n======== Get Rendered Prompt ========\n");

        // Create kernel instance
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: s_openAIModelId!,
                apiKey: s_openAIApiKey!)
            .Build();

        // Initialize prompt
        const string FunctionPrompt = "Write a random paragraph about: {{$input}} in the style of {{$style}}.";

        var excuseFunction = kernel.CreateFunctionFromPrompt(
            FunctionPrompt,
            functionName: "Excuse",
            executionSettings: new OpenAIPromptExecutionSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        // Define hooks
        void MyRenderingHandler(object? sender, PromptRenderingEventArgs e)
        {
            Console.WriteLine($"{e.Function.Name} : Prompt Rendering Handler - Triggered");
            e.Arguments["style"] = "Seinfeld";
        }

        void MyRenderedHandler(object? sender, PromptRenderedEventArgs e)
        {
            Console.WriteLine($"{e.Function.Name} : Prompt Rendered Handler - Triggered");
            e.RenderedPrompt += " USE SHORT, CLEAR, COMPLETE SENTENCES.";

            Console.WriteLine(e.RenderedPrompt);
        }

        kernel.PromptRendering += MyRenderingHandler;
        kernel.PromptRendered += MyRenderedHandler;

        // Invoke prompt to trigger prompt rendering hooks.
        const string Input = "I missed the F1 final race";
        var result = await kernel.InvokeAsync(excuseFunction, new() { ["input"] = Input });
        Console.WriteLine($"Function Result: {result.GetValue<string>()}");
    }

    /// <summary>
    /// Demonstrate using kernel invocation-hooks to post process result:
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static async Task ChangingResultAsync()
    {
        Console.WriteLine("\n======== Changing/Filtering Function Result ========\n");

        // Create kernel instance
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
               modelId: s_openAIModelId!,
               apiKey: s_openAIApiKey!)
            .Build();

        // Initialize function
        const string FunctionPrompt = "Write a paragraph about Handlers.";

        var writerFunction = kernel.CreateFunctionFromPrompt(
            FunctionPrompt,
            functionName: "Writer",
            executionSettings: new OpenAIPromptExecutionSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        // Define hook
        static void MyChangeDataHandler(object? sender, FunctionInvokedEventArgs e)
        {
            var originalOutput = e.Result.ToString();

            //Use Regex to redact all vowels and numbers
            var newOutput = Regex.Replace(originalOutput, "[aeiouAEIOU0-9]", "*");

            e.SetResultValue(newOutput);
        }

        kernel.FunctionInvoked += MyChangeDataHandler;

        // Invoke prompt to trigger execution hooks.
        var result = await kernel.InvokeAsync(writerFunction);

        Console.WriteLine($"Function Result: {result.GetValue<string>()}");
    }

    /// <summary>
    /// Demonstrate using kernel invocation-hooks to cancel prior to execution:
    /// <see cref="Kernel.FunctionInvoking"/>
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static async Task BeforeInvokeCancellationAsync()
    {
        Console.WriteLine("\n======== Cancelling Pipeline Execution - Invoking event ========\n");

        // Create kernel instance
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
               modelId: s_openAIModelId!,
               apiKey: s_openAIApiKey!)
            .Build();

        // Initialize prompt
        const string FunctionPrompt = "Write a paragraph about: Cancellation.";

        var writerFunction = kernel.CreateFunctionFromPrompt(
            FunctionPrompt,
            functionName: "Writer",
            executionSettings: new OpenAIPromptExecutionSettings() { MaxTokens = 1000, Temperature = 1, TopP = 0.5 });

        // Adding new inline handler to cancel/prevent function execution
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            Console.WriteLine($"{e.Function.Name} : FunctionInvoking - Cancelling before execution");
            e.Cancel = true;
        };

        // Technically invoked will never be called since the function will be cancelled
        int functionInvokedCount = 0;
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            functionInvokedCount++;
        };

        // Invoke prompt to trigger execution hooks.
        var result = await kernel.InvokeAsync(writerFunction);
        Console.WriteLine($"Function Invocation Times: {functionInvokedCount}");
    }

    /// <summary>
    /// Demonstrate using kernel invocation-hooks to cancel post after execution:
    /// <see cref="Kernel.FunctionInvoking"/>
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static async Task AfterInvokeCancellationAsync()
    {
        Console.WriteLine("\n======== Cancelling Pipeline Execution - Invoked event ========\n");

        // Create kernel instance
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
               modelId: s_openAIModelId!,
               apiKey: s_openAIApiKey!)
            .Build();

        // Initialize prompts
        int functionInvokingCount = 0;
        int functionInvokedCount = 0;

        var firstFunction = kernel.CreateFunctionFromPrompt("Write a phrase with Invoke.", functionName: "InvokePhrase");
        var secondFunction = kernel.CreateFunctionFromPrompt("Write a phrase with Cancellation.", functionName: "CancellationPhrase");

        // Adding new inline handler to count invoking events
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            functionInvokingCount++;
        };

        // Invoked will never be called twice (for the secondFunction) since Invoked from the first is cancelling.
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            functionInvokedCount++;
            e.Cancel = true;
        };

        // Invoke prompt to trigger execution hooks.
        var result = await kernel.InvokeAsync(secondFunction);
        Console.WriteLine($"Function Invoked Times: {functionInvokedCount}");
        Console.WriteLine($"Function Invoking Times: {functionInvokingCount}");
    }
}
