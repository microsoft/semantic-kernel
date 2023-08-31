// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Action;
using RepoUtils;


// ReSharper disable once InconsistentNaming
public static class Example28_ActionPlanner
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Action Planner ========");
        var builder = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);

        // var builder = new KernelBuilder()
        //     .WithLoggerFactory(ConsoleLogger.LoggerFactory)
        //     .WithOpenAIChatCompletionService(
        //         TestConfiguration.OpenAI.ChatModelId,
        //         TestConfiguration.OpenAI.ApiKey);

        string folder = RepoFiles.SampleSkillsPath();
        IKernel kernel = builder.Build();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel.ImportSemanticSkillFromDirectory(folder, "FunSkill");

        // We're going to ask the planner to find a function to achieve this goal.
        var goal = "Write a joke about Cleopatra in the style of Hulk Hogan.";

        // The planner returns a plan, consisting of a single function
        // to execute and achieve the goal requested.
        // var plan = await planner.CreatePlanAsync(goal);
        // Execute the full plan (which is a single function)
        SKContext result = await UseActionPlanner(kernel, goal).ConfigureAwait(false);

        //Show the result, which should match the given goal
        Console.WriteLine(result);

        IKernel kernel2 = builder.Build();
        kernel2.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
        kernel2.ImportSemanticSkillFromDirectory(folder, "WriterSkill");
        kernel2.ImportSemanticSkillFromDirectory(folder, "FunSkill");
        SKContext structuredResult = await UseStructuredActionPlanner(kernel2, goal).ConfigureAwait(false);

        Console.WriteLine(structuredResult);
        /* Output:
         * Why did Cleopatra refuse to wrestle Hulk Hogan at the office party?
         * Because she heard he was the king of "de-Nile" moves!
         */

        /* Usage: ActionPlanner
         * Total tokens: 1179 + 148 = 1327 (plan + execution respectively)
         * Total prompt tokens: 1123 + 105 = 1228 (plan + execution respectively)
         * Total completion tokens: 56 + 43 = 99 (plan + execution respectively)
         */

        /* Usage: StructuredActionPlanner
         * Total tokens: 709 + 136 = 845 (plan + execution respectively)
         * Total prompt tokens: 584 + 105 = 689 (plan + execution respectively)
         * Total completion tokens: 125 + 31 = 156 (plan + execution respectively)
         */
    }


    private static async Task<SKContext> UseActionPlanner(IKernel kernel, string goal)
    {
        // Create an instance of ActionPlanner.
        // The ActionPlanner takes one goal and returns a single function to execute.
        var planner = new ActionPlanner(kernel);

        // The planner returns a plan, consisting of a single function
        // to execute and achieve the goal requested.
        var plan = await planner.CreatePlanAsync(goal);
        return await plan.InvokeAsync();
    }


    private static async Task<SKContext> UseStructuredActionPlanner(IKernel kernel, string goal)
    {
        var planner = new StructuredActionPlanner(kernel);
        var plan = await planner.CreatePlanAsync(goal);
        return await plan.InvokeAsync();
    }
}
