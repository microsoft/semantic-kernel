// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once InconsistentNaming

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example09_FunctionTypes
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Native function types ========");

        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var variables = new ContextVariables();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        var plugin = kernel.ImportPluginFromObject<LocalExamplePlugin>("test");

        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));

        // Using Kernel.InvokeAsync
        await kernel.InvokeAsync(plugin["type01"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type01"]);

        await kernel.InvokeAsync(plugin["type02"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type02"]);

        await kernel.InvokeAsync(plugin["type03"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type03"]);

        await kernel.InvokeAsync(plugin["type04"], variables);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type04"], variables);

        await kernel.InvokeAsync(plugin["type05"], variables);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type05"], variables);

        await kernel.InvokeAsync(plugin["type06"], variables);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type06"], variables);

        await kernel.InvokeAsync(plugin["type07"], variables);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type07"], variables);

        await kernel.InvokeAsync(plugin["type08"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type08"]);

        await kernel.InvokeAsync(plugin["type09"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type09"]);

        await kernel.InvokeAsync(plugin["type10"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type10"]);

        await kernel.InvokeAsync(plugin["type11"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type11"]);

        await kernel.InvokeAsync(plugin["type12"], variables);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type12"], variables);

        await kernel.InvokeAsync(plugin["type18"]);
        await kernel.InvokeAsync(kernel.Plugins["test"]["type18"]);
    }
}

public class LocalExamplePlugin
{
    [SKFunction]
    public void Type01()
    {
        Console.WriteLine("Running function type 1");
    }

    [SKFunction]
    public string Type02()
    {
        Console.WriteLine("Running function type 2");
        return "";
    }

    [SKFunction]
    public async Task<string> Type03Async()
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 3");
        return "";
    }

    [SKFunction]
    public void Type04(SKContext context)
    {
        Console.WriteLine("Running function type 4");
    }

    [SKFunction]
    public string Type05(SKContext context)
    {
        Console.WriteLine("Running function type 5");
        return "";
    }

    [SKFunction]
    public async Task<string> Type06Async(Kernel kernel)
    {
        var summary = await kernel.InvokeAsync(kernel.Plugins["SummarizePlugin"]["Summarize"], new ContextVariables("blah blah blah"));
        Console.WriteLine($"Running function type 6 [{summary?.GetValue<string>()}]");
        return "";
    }

    [SKFunction]
    public async Task<SKContext> Type07Async(SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 7");
        return context;
    }

    [SKFunction]
    public void Type08(string x)
    {
        Console.WriteLine("Running function type 8");
    }

    [SKFunction]
    public string Type09(string x)
    {
        Console.WriteLine("Running function type 9");
        return "";
    }

    [SKFunction]
    public async Task<string> Type10Async(string x)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 10");
        return "";
    }

    [SKFunction]
    public void Type11(string x, SKContext context)
    {
        Console.WriteLine("Running function type 11");
    }

    [SKFunction]
    public string Type12(string x, SKContext context)
    {
        Console.WriteLine("Running function type 12");
        return "";
    }

    [SKFunction]
    public async Task<string> Type13Async(string x, SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 13");
        return "";
    }

    [SKFunction]
    public async Task<SKContext> Type14Async(string x, SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 14");
        return context;
    }

    [SKFunction]
    public async Task Type15Async(string x)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 15");
    }

    [SKFunction]
    public async Task Type16Async(SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 16");
    }

    [SKFunction]
    public async Task Type17Async(string x, SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 17");
    }

    [SKFunction]
    public async Task Type18Async()
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 18");
    }
}
