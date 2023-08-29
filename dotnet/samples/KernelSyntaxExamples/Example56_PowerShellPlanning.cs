// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.PowerShell;
using RepoUtils;

namespace KernelSyntaxExamples;

// ReSharper disable once InconsistentNaming
public static class Example56_PowerShellPlanning
{
    public static async Task RunAsync()
    {
        const string goal = "Write a poem about John Doe, then translate it into Italian.";

        Console.WriteLine($"Goal: {goal}");

        var kernel = GetKernel();
        var context = kernel.CreateNewContext();
        var generator = new ScriptGenerator(kernel);

        var script = await generator.GenerateScriptAsync(goal);

        Console.WriteLine("Generated script:\n");
        Console.WriteLine(script);

        var plan = script.ToPlanFromScript(goal, context);

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.Result);

        Console.ReadKey();
    }

    private static IKernel GetKernel()
    {
        var folder = RepoFiles.SampleSkillsPath();

        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill", "WriterSkill");

        return kernel;
    }
}
