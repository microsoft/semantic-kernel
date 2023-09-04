// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.PowerShell;
using RepoUtils;

namespace KernelSyntaxExamples;

// ReSharper disable once InconsistentNaming
public static class Example56_PowerShellPlanner
{
    public static async Task RunAsync()
    {
        const string Goal = "Write a poem about John Doe, then translate it into Italian.";

        Console.WriteLine($"Goal: {Goal}");

        var kernel = GetKernel();

        var planner = new PowerShellPlanner(kernel);

        var plan = await planner.CreatePlanAsync(Goal);

        Console.WriteLine("Generated plan:\n");
        Console.WriteLine(plan.OriginalPlan);

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("\nResult:");
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
