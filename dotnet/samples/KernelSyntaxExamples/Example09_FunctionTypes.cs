// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once InconsistentNaming

using System;
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

        var kernel = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var fakeContext = new SKContext(kernel);

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        var testFunctions = kernel.ImportFunctions(new LocalExamplePlugin(), "test");

        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportSemanticFunctionsFromDirectory(folder, "SummarizePlugin");

        // The kernel takes care of wiring the input appropriately
        await kernel.RunAsync(
            testFunctions["type01"],
            testFunctions["type02"],
            testFunctions["type03"],
            testFunctions["type04"],
            testFunctions["type05"],
            testFunctions["type06"],
            testFunctions["type07"],
            testFunctions["type08"],
            testFunctions["type09"],
            testFunctions["type10"],
            testFunctions["type11"],
            testFunctions["type12"],
            testFunctions["type13"],
            testFunctions["type14"],
            testFunctions["type15"],
            testFunctions["type16"],
            testFunctions["type17"],
            testFunctions["type18"]
        );

        // Using Kernel.RunAsync
        await kernel.RunAsync(testFunctions["type01"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type01"));

        await kernel.RunAsync(testFunctions["type02"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type02"));

        await kernel.RunAsync(testFunctions["type03"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type03"));

        await kernel.RunAsync(testFunctions["type04"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type04"));

        await kernel.RunAsync(testFunctions["type05"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type05"));

        await kernel.RunAsync(testFunctions["type06"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type06"));

        await kernel.RunAsync(testFunctions["type07"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type07"));

        await kernel.RunAsync("", testFunctions["type08"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type08"));

        await kernel.RunAsync("", testFunctions["type09"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type09"));

        await kernel.RunAsync("", testFunctions["type10"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type10"));

        await kernel.RunAsync("", testFunctions["type11"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type11"));

        await kernel.RunAsync(fakeContext.Variables, testFunctions["type12"]);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type12"));

        await kernel.RunAsync(testFunctions["type18"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type18"));
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
    public async Task<string> Type06Async(SKContext context)
    {
        var summarizer = context.Functions.GetFunction("SummarizePlugin", "Summarize");
        var summary = await context.Kernel.RunAsync("blah blah blah", summarizer);

        Console.WriteLine($"Running function type 6 [{summary.GetValue<string>()}]");
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
