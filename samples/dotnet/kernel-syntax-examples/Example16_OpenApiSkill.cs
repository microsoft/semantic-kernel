// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;
using RepoUtils;

namespace KernelSyntaxExamples;
internal class Example16_OpenApiSkill
{
    public static async Task RunAsync()
    {
        await GetSecretFromAzureKeyValutAsync();
    }

    public static async Task GetSecretFromAzureKeyValutAsync()
    {
        Console.WriteLine("======== Planning - Create and Execute Azure Plan ========");
        var kernel = InitializeKernelAndPlanner(out var planner);

        //Use OpenApi skill from folder
        //string folder = RepoFiles.SampleSkillsPath();
        //kernel.ImportOpenApiSkillFromDirectory(folder, "AzureKeyVaultSkill");

        //Use OpenApi skill from Skills.OpenAPI package
        kernel.ImportOpenApiSkillFromResource(SkillResourceNames.AzureKeyVault);

        var plan = await kernel.RunAsync("Load 'test-secret' from Azure KeyValut available at https://dev-tests.vault.azure.net using GetSecret function.", planner["CreatePlan"]);

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.Variables.ToPlan().PlanString);

        await ExecutePlanAsync(kernel, planner, plan, 5);
    }

    private static IKernel InitializeKernelAndPlanner(out IDictionary<string, ISKFunction> planner)
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddAzureOpenAICompletionBackend(
            Env.Var("AZURE_OPENAI_DEPLOYMENT_LABEL"),
            Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY"));

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        planner = kernel.ImportSkill(new PlannerSkill(kernel), "planning");

        return kernel;
    }

    private static async Task<SKContext> ExecutePlanAsync(
        IKernel kernel,
        IDictionary<string, ISKFunction> planner,
        SKContext executionResults,
        int maxSteps = 10)
    {
        Stopwatch sw = new();
        sw.Start();

        // loop until complete or at most N steps
        for (int step = 1; !executionResults.Variables.ToPlan().IsComplete && step < maxSteps; step++)
        {
            var results = await kernel.RunAsync(executionResults.Variables, planner["ExecutePlan"]);
            if (results.Variables.ToPlan().IsSuccessful)
            {
                Console.WriteLine($"Step {step} - Execution results:");
                Console.WriteLine(results.Variables.ToPlan().PlanString);

                if (results.Variables.ToPlan().IsComplete)
                {
                    Console.WriteLine($"Step {step} - COMPLETE!");
                    Console.WriteLine(results.Variables.ToPlan().Result);

                    // Console.WriteLine("VARIABLES: ");
                    // Console.WriteLine(string.Join("\n\n", results.Variables.Select(v => $"{v.Key} = {v.Value}")));
                    break;
                }

                // Console.WriteLine($"Step {step} - Results so far:");
                // Console.WriteLine(results.ToPlan().Result);
            }
            else
            {
                Console.WriteLine($"Step {step} - Execution failed:");
                Console.WriteLine(results.Variables.ToPlan().Result);
                break;
            }

            executionResults = results;
        }

        sw.Stop();
        Console.WriteLine($"Execution complete in {sw.ElapsedMilliseconds} ms!");
        return executionResults;
    }
}
