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

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        var test = kernel.ImportPlugin(new LocalExampleSkill(), "test");

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticPluginFromDirectory(folder, "SummarizeSkill");

        // The kernel takes care of wiring the input appropriately
        await kernel.RunAsync(
            test["type01"],
            test["type02"],
            test["type03"],
            test["type04"],
            test["type05"],
            test["type06"],
            test["type07"],
            test["type08"],
            test["type09"],
            test["type10"],
            test["type11"],
            test["type12"],
            test["type13"],
            test["type14"],
            test["type15"],
            test["type16"],
            test["type17"],
            test["type18"]
        );

        // Using Kernel.RunAsync
        await kernel.RunAsync(test["type01"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type01"));

        await kernel.RunAsync(test["type02"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type02"));

        await kernel.RunAsync(test["type03"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type03"));

        await kernel.RunAsync(test["type04"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type04"));

        await kernel.RunAsync(test["type05"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type05"));

        await kernel.RunAsync(test["type06"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type06"));

        await kernel.RunAsync(test["type07"], fakeContext.Variables);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type07"));

        await kernel.RunAsync("", test["type08"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type08"));

        await kernel.RunAsync("", test["type09"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type09"));

        await kernel.RunAsync("", test["type10"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type10"));

        await kernel.RunAsync("", test["type11"]);
        await kernel.RunAsync("", kernel.Functions.GetFunction("test", "type11"));

        await kernel.RunAsync(fakeContext.Variables, test["type12"]);
        await kernel.RunAsync(fakeContext.Variables, kernel.Functions.GetFunction("test", "type12"));

        await kernel.RunAsync(test["type18"]);
        await kernel.RunAsync(kernel.Functions.GetFunction("test", "type18"));
    }
}

public class LocalExampleSkill
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
        var summarizer = context.Functions.GetFunction("SummarizeSkill", "Summarize");
        var summary = await context.Kernel.RunAsync("blah blah blah", summarizer);

        Console.WriteLine($"Running function type 6 [{summary}]");
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
