// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once InconsistentNaming

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
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

        var fakeContext = new SKContext(kernel, loggerFactory: ConsoleLogger.LoggerFactory);

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        var test = kernel.ImportSkill(new LocalExampleSkill(), "test");

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");

        // The kernel takes care of wiring the input appropriately
        await kernel.RunAsync(
            "",
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

        await kernel.Func("test", "type01").InvokeAsync(kernel);
        await test["type01"].InvokeAsync(kernel);

        await kernel.Func("test", "type02").InvokeAsync(kernel);
        await test["type02"].InvokeAsync(kernel);

        await kernel.Func("test", "type03").InvokeAsync(kernel);
        await test["type03"].InvokeAsync(kernel);

        await kernel.Func("test", "type04").InvokeAsync(fakeContext);
        await test["type04"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type05").InvokeAsync(fakeContext);
        await test["type05"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type06").InvokeAsync(fakeContext);
        await test["type06"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type07").InvokeAsync(fakeContext);
        await test["type07"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type08").InvokeAsync("", kernel);
        await test["type08"].InvokeAsync("", kernel);

        await kernel.Func("test", "type09").InvokeAsync("", kernel);
        await test["type09"].InvokeAsync("", kernel);

        await kernel.Func("test", "type10").InvokeAsync("", kernel);
        await test["type10"].InvokeAsync("", kernel);

        await kernel.Func("test", "type11").InvokeAsync("", kernel);
        await test["type11"].InvokeAsync("", kernel);

        await kernel.Func("test", "type12").InvokeAsync(fakeContext);
        await test["type12"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type18").InvokeAsync(kernel);
        await test["type18"].InvokeAsync(kernel);
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
        var summarizer = context.skills.GetFunction("SummarizeSkill", "Summarize");

        var summary = await summarizer.InvokeAsync("blah blah blah", context.Kernel);

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
