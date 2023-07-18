// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example54_PlanHooks
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Sequential Planner - Using Step Hooks ========");
        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithAzureTextCompletionService(
                TestConfiguration.AzureOpenAI.DeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder,
            "SummarizeSkill",
            "WriterSkill");

        var planner = new SequentialPlanner(kernel);

        var plan = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanString());

        plan.SetStepsPreExecutionHook(MyPreHook);
        plan.SetStepsPostExecutionHook(MyPostHook);

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.Result);

        SKContext MyPreHook(SKContext context, string generatedPrompt)
        {
            Console.WriteLine($"Pre Hook - Prompt: {generatedPrompt}");
            return context;
        }

        SKContext MyPostHook(SKContext context)
        {
            Console.WriteLine($"Post Hook - Total Tokens: {context.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");
            return context;
        }
    }
}
