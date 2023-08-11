// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example55_PlanHandlers
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Sequential Planner - Using Step Execution Handlers ========");
        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Logger)
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

        plan.SetPreExecutionHandler(MyPreHandler);
        plan.SetPostExecutionHandler(MyPostHandler);

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.Result);

        Task MyPreHandler(PreExecutionContext executionContext)
        {
            Console.WriteLine($"Pre Execution Handler - Prompt: {executionContext.Prompt}");

            return Task.CompletedTask;
        }

        Task MyPostHandler(PostExecutionContext executionContext)
        {
            Console.WriteLine($"Post Execution Handler - Total Tokens: {executionContext.SKContext.ModelResults.First().GetOpenAITextResult().Usage.TotalTokens}");

            return Task.CompletedTask;
        }
    }
}
