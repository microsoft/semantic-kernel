// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once InconsistentNaming

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example09_FunctionTypes
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Native function types ========");

        var fakeContext = new SKContext(new ContextVariables(), NullMemory.Instance, null, ConsoleLogger.Log);

        var kernel = Kernel.Builder.WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddOpenAICompletionBackend("text-davinci-003", "text-davinci-003", Env.Var("OPENAI_API_KEY"));

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

        await kernel.Func("test", "type01").InvokeAsync();
        await test["type01"].InvokeAsync();

        await kernel.Func("test", "type02").InvokeAsync();
        await test["type02"].InvokeAsync();

        await kernel.Func("test", "type03").InvokeAsync();
        await test["type03"].InvokeAsync();

        await kernel.Func("test", "type04").InvokeAsync(fakeContext);
        await test["type04"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type05").InvokeAsync(fakeContext);
        await test["type05"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type06").InvokeAsync(fakeContext);
        await test["type06"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type07").InvokeAsync(fakeContext);
        await test["type07"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type08").InvokeAsync("");
        await test["type08"].InvokeAsync("");

        await kernel.Func("test", "type09").InvokeAsync("");
        await test["type09"].InvokeAsync("");

        await kernel.Func("test", "type10").InvokeAsync("");
        await test["type10"].InvokeAsync("");

        await kernel.Func("test", "type11").InvokeAsync("", fakeContext);
        await test["type11"].InvokeAsync("", fakeContext);

        await kernel.Func("test", "type12").InvokeAsync("", fakeContext);
        await test["type12"].InvokeAsync("", fakeContext);

        await kernel.Func("test", "type13").InvokeAsync("", fakeContext);
        await test["type13"].InvokeAsync("", fakeContext);

        await kernel.Func("test", "type14").InvokeAsync("", fakeContext);
        await test["type14"].InvokeAsync("", fakeContext);

        await kernel.Func("test", "type15").InvokeAsync("");
        await test["type15"].InvokeAsync("");

        await kernel.Func("test", "type16").InvokeAsync(fakeContext);
        await test["type16"].InvokeAsync(fakeContext);

        await kernel.Func("test", "type17").InvokeAsync("", fakeContext);
        await test["type17"].InvokeAsync("", fakeContext);

        await kernel.Func("test", "type18").InvokeAsync();
        await test["type18"].InvokeAsync();
    }
}

public class LocalExampleSkill
{
    [SKFunction(Description = "Native function type 1")]
    public void Type01()
    {
        Console.WriteLine("Running function type 1");
    }

    [SKFunction(Description = "Native function type 2")]
    public string Type02()
    {
        Console.WriteLine("Running function type 2");
        return "";
    }

    [SKFunction(Name = "Type03", Description = "Native function type 3")]
    public async Task<string> Type03Async()
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 3");
        return "";
    }

    [SKFunction(Description = "Native function type 4")]
    public void Type04(SKContext context)
    {
        Console.WriteLine("Running function type 4");
    }

    [SKFunction(Description = "Native function type 5")]
    public string Type05(SKContext context)
    {
        Console.WriteLine("Running function type 5");
        return "";
    }

    [SKFunction(Name = "Type06", Description = "Native function type 6")]
    public async Task<string> Type06Async(SKContext context)
    {
        var summarizer = context.Func("SummarizeSkill", "Summarize");

        var summary = await summarizer.InvokeAsync("blah blah blah");

        Console.WriteLine($"Running function type 6 [{summary}]");
        return "";
    }

    [SKFunction(Name = "Type07", Description = "Native function type 7")]
    public async Task<SKContext> Type07Async(SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 7");
        return context;
    }

    [SKFunction(Description = "Native function type 8")]
    public void Type08(string x)
    {
        Console.WriteLine("Running function type 8");
    }

    [SKFunction(Description = "Native function type 9")]
    public string Type09(string x)
    {
        Console.WriteLine("Running function type 9");
        return "";
    }

    [SKFunction(Name = "Type10", Description = "Native function type 10")]
    public async Task<string> Type10Async(string x)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 10");
        return "";
    }

    [SKFunction(Description = "Native function type 11")]
    public void Type11(string x, SKContext context)
    {
        Console.WriteLine("Running function type 11");
    }

    [SKFunction(Description = "Native function type 12")]
    public string Type12(string x, SKContext context)
    {
        Console.WriteLine("Running function type 12");
        return "";
    }

    [SKFunction(Name = "Type13", Description = "Native function type 13")]
    public async Task<string> Type13Async(string x, SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 13");
        return "";
    }

    [SKFunction(Name = "Type14", Description = "Native function type 14")]
    public async Task<SKContext> Type14Async(string x, SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 14");
        return context;
    }

    [SKFunction(Name = "Type15", Description = "Native function type 15")]
    public async Task Type15Async(string x)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 15");
    }

    [SKFunction(Name = "Type16", Description = "Native function type 16")]
    public async Task Type16Async(SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 16");
    }

    [SKFunction(Name = "Type17", Description = "Native function type 17")]
    public async Task Type17Async(string x, SKContext context)
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 17");
    }

    [SKFunction(Name = "Type18", Description = "Native function type 18")]
    public async Task Type18Async()
    {
        await Task.Delay(0);
        Console.WriteLine("Running function type 18");
    }
}
