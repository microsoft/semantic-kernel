// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Action;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example28_ActionPlanner
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Action Planner ========");
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");

        // Create an optional config for the ActionPlanner. Use this to exclude skills and functions if needed
        var config = new ActionPlannerConfig();
        config.ExcludedFunctions.Add("MakeAbstractReadable");

        // Create an instance of ActionPlanner.
        // The ActionPlanner takes one goal and returns a single function to execute.
        var planner = new ActionPlanner(kernel, config: config);

        // We're going to ask the planner to find a function to achieve this goal.
        var goal = "Write a joke about Cleopatra in the style of Hulk Hogan.";

        // The planner returns a plan, consisting of a single function
        // to execute and achieve the goal requested.
        var plan = await planner.CreatePlanAsync(goal);

        // Execute the full plan (which is a single function)
        var result = await plan.InvokeAsync();

        // Show the result, which should match the given goal
        Console.WriteLine(result.GetValue<string>());

        /* Output:
         *
         * Cleopatra was a queen
         * But she didn't act like one
         * She was more like a teen

         * She was always on the scene
         * And she loved to be seen
         * But she didn't have a queenly bone in her body
         */
    }
}
