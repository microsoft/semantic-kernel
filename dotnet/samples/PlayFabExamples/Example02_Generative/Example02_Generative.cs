// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using PlayFabExamples.Common.Configuration;
using PlayFabExamples.Common.Logging;

namespace PlayFabExamples.Example02_Generative;
public static class Example02_Generative
{
    public static async Task RunAsync()
    {
        var goals = new string[]
            {
                "Create a segment with name NewPlayersSegment for the players first logged in date greater than 2023-08-01?", // Working
                "Create a segment with name LegacyPlayersSegment for the players last logged in date less than 2023-05-01?", // Working
                "Create a segment with name EgyptNewPlayers for the players located in the Egypt?", // Working
                "Create a segment with name ChinaPlayers for the players in china and grant them 10 VC virtual currency?", // Working
                //"Create a segment with name ChinaNewPlayers for the players in china who first logged in the last 30 days and grant them 10 virtual currency?",
                //"Create a segment with name WelcomeEgyptNewPlayers for the players located in the Egypt with entered segment action of email notification?", // With entered segment action
                //"Create a segment with name EgyptNewPlayers for the players located in the Egypt?" // If the segment already exist, create a segment with name appended with guid
            };

        foreach (string prompt in goals)
        {
            try
            {
                await CreateSegmentExample(prompt);
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.ToString());
            }
        }
    }

    private static async Task CreateSegmentExample(string goal)
    {
        // Create a segment skill
        Console.WriteLine("======== Action Planner ========");
        var kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Logger)
            .WithAzureTextCompletionService(TestConfiguration.AzureOpenAI.DeploymentName, TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        kernel.ImportSkill(new SegmentSkill(), "SegmentSkill");

        // Create an instance of ActionPlanner.
        // The ActionPlanner takes one goal and returns a single function to execute.
        var planner = new ActionPlanner(kernel);

        // We're going to ask the planner to find a function to achieve this goal.
        //var goal = "Create a segment with name NewPlayersSegment for the players first logged in date greater than 2023-08-01?";
        Console.WriteLine("Goal: " + goal);

        // The planner returns a plan, consisting of a single function
        // to execute and achieve the goal requested.
        var plan = await planner.CreatePlanAsync(goal);
        plan.Steps[0].Parameters = plan.Parameters;

        // Execute the full plan (which is a single function)
        SKContext result = await plan.InvokeAsync(kernel.CreateNewContext());

        // Show the result, which should match the given goal
        Console.WriteLine(result);
    }
}
