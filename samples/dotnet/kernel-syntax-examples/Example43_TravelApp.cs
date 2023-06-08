// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Sequential;
using Skills;
using Skills.Weather.WeatherApi;
using RepoUtils;

// ReSharper disable CommentTypo
// ReSharper disable once InconsistentNaming
internal static class Example43_TravelApp
{
    public static async Task RunAsync(string ask)
    {
        await GoToNeighborHouse(ask);
    }

    private static async Task GoToNeighborHouse(string ask)
    {
        Console.WriteLine("======== Sequential Planner - Create and Execute Poetry Plan ========");

        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithAzureTextCompletionService(
                Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_ENDPOINT"),
                Env.Var("AZURE_OPENAI_KEY"))
            .Build();

        string folder = @"C:\semantic-kernel\samples\dotnet\kernel-syntax-examples\Skills";//RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder,
            "TravelPreparation");

        folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder,
            "SummarizeSkill",
            "WriterSkill");

        using var weatherConnector = new WeatherApiConnector(Env.Var("WeatherApiKey"));
        kernel.ImportSkill(new WeatherLookupSkill(weatherConnector), "weatherapi");

        var planner = new SequentialPlanner(kernel);

        var plan = await planner.CreatePlanAsync(ask);

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanString());

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.Result);
    }
    private static IKernel InitializeKernelAndPlanner(out SequentialPlanner planner, int maxTokens = 1024)
    {
        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithAzureTextCompletionService(
                Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_ENDPOINT"),
                Env.Var("AZURE_OPENAI_KEY"))
            .Build();

        planner = new SequentialPlanner(kernel, new SequentialPlannerConfig { MaxTokens = maxTokens });

        return kernel;
    }

    private static async Task<Plan> ExecutePlanAsync(
        IKernel kernel,
        Plan plan,
        string input = "",
        int maxSteps = 10)
    {
        Stopwatch sw = new();
        sw.Start();

        // loop until complete or at most N steps
        try
        {
            for (int step = 1; plan.HasNextStep && step < maxSteps; step++)
            {
                if (string.IsNullOrEmpty(input))
                {
                    await plan.InvokeNextStepAsync(kernel.CreateNewContext());
                    // or await kernel.StepAsync(plan);
                }
                else
                {
                    plan = await kernel.StepAsync(input, plan);
                }

                if (!plan.HasNextStep)
                {
                    Console.WriteLine($"Step {step} - COMPLETE!");
                    Console.WriteLine(plan.State.ToString());
                    break;
                }

                Console.WriteLine($"Step {step} - Results so far:");
                Console.WriteLine(plan.State.ToString());
            }
        }
        catch (KernelException e)
        {
            Console.WriteLine("Step - Execution failed:");
            Console.WriteLine(e.Message);
        }

        sw.Stop();
        Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        return plan;
    }
}
