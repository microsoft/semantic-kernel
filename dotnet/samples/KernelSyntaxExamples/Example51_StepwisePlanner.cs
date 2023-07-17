// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using NCalcSkills;
using RepoUtils;

/**
 * This example shows how to use Stepwise Planner to create a plan for a given goal.
 */

// ReSharper disable once InconsistentNaming
public static class Example51_StepwisePlanner
{
    public static async Task RunAsync()
    {
        string[] questions = new string[]
        {
            "Who is the current president of the United States? What is his current age divided by 2",
            // "Who is Leo DiCaprio's girlfriend? What is her current age raised to the (his current age)/100 power?",
            // "What is the capital of France? Who is that cities current mayor? What percentage of their life has been in the 21st century as of today?",
            // "What is the current day of the calendar year? Using that as an angle in degrees, what is the area of a unit circle with that angle?"
        };

        foreach (var question in questions)
        {
            await RunTextCompletion(question);
            await RunChatCompletion(question);
        }
    }

    private static async Task RunTextCompletion(string question)
    {
        Console.WriteLine("RunTextCompletion");
        var kernel = GetKernel();
        await RunWithQuestion(kernel, question);
    }

    private static async Task RunChatCompletion(string question)
    {
        Console.WriteLine("RunChatCompletion");
        var kernel = GetKernel(true);
        await RunWithQuestion(kernel, question);
    }

    private static async Task RunWithQuestion(IKernel kernel, string question)
    {
        var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);

        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "advancedCalculator");
        // kernel.ImportSkill(new SimpleCalculatorSkill(kernel), "basicCalculator");
        kernel.ImportSkill(new TimeSkill(), "time");

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        Console.WriteLine("Question: " + question);

        var plannerConfig = new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig();
        plannerConfig.ExcludedFunctions.Add("TranslateMathProblem");
        plannerConfig.MinIterationTimeMs = 1500;
        plannerConfig.MaxTokens = 4000;

        StepwisePlanner planner = new(kernel, plannerConfig);
        sw.Start();
        var plan = planner.CreatePlan(question);

        var result = await plan.InvokeAsync(kernel.CreateNewContext());
        Console.WriteLine("Result: " + result);
        if (result.Variables.TryGetValue("stepCount", out string? stepCount))
        {
            Console.WriteLine("Steps Taken: " + stepCount);
        }

        if (result.Variables.TryGetValue("skillCount", out string? skillCount))
        {
            Console.WriteLine("Skills Used: " + skillCount);
        }

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        Console.WriteLine("*****************************************************");
    }

    private static IKernel GetKernel(bool useChat = false)
    {
        var builder = new KernelBuilder();
        if (useChat)
        {
            builder.WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey,
                alsoAsTextCompletion: true,
                setAsDefault: true);
        }
        else
        {
            builder.WithAzureTextCompletionService(
                TestConfiguration.AzureOpenAI.DeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }

        var kernel = builder
            .WithLogger(ConsoleLogger.Log)
            .Configure(c => c.SetDefaultHttpRetryConfig(new HttpRetryConfig
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                MinRetryDelay = TimeSpan.FromSeconds(3),
            }))
            .Build();

        return kernel;
    }
}

// RunTextCompletion
// *****************************************************
// Question: Who is the current president of the United States? What is his current age divided by 2
// Result: The current president of the United States is Joe Biden. His current age divided by 2 is 40.
// Steps Taken: 10
// Skills Used: 4 (WebSearch.Search(2), time.Date(1), advancedCalculator.Calculator(1))
// Time Taken: 00:00:53.6331324
// *****************************************************
// RunChatCompletion
// *****************************************************
// Question: Who is the current president of the United States? What is his current age divided by 2
// Result: The current president of the United States is Joe Biden. His current age divided by 2 is 40.5.
// Steps Taken: 9
// Skills Used: 7 (WebSearch.Search(4), time.Year(1), time.Date(1), advancedCalculator.Calculator(1))
// Time Taken: 00:01:13.3766860
// *****************************************************
// RunTextCompletion
// *****************************************************
// Question: Who is Leo DiCaprio's girlfriend? What is her current age raised to the (his current age)/100 power?
// Result: Leo DiCaprio's girlfriend is Camila Morrone. Her current age raised to the (his current age)/100 power is 4.935565735151678.
// Steps Taken: 6
// Skills Used: 5 (WebSearch.Search(3), time.Year(1), advancedCalculator.Calculator(1))
// Time Taken: 00:00:37.8941510
// *****************************************************
// RunChatCompletion
// *****************************************************
// Question: Who is Leo DiCaprio's girlfriend? What is her current age raised to the (his current age)/100 power?
// Result: Leo DiCaprio's girlfriend is Camila Morrone. Her current age raised to the power of (his current age)/100 is approximately 4.94.
// Steps Taken: 9
// Skills Used: 5 (WebSearch.Search(3), time.Year(1), advancedCalculator.Calculator(1))
// Time Taken: 00:01:17.6742136
// *****************************************************
// RunTextCompletion
// *****************************************************
// Question: What is the capital of France? Who is that cities current mayor? What percentage of their life has been in the 21st century as of today?
// Result: The capital of France is Paris. The current mayor of Paris is Anne Hidalgo. She has spent 36.51% of her life in the 21st century as of 2023.
// Steps Taken: 7
// Skills Used: 4 (WebSearch.Search(3), advancedCalculator.Calculator(1))
// Time Taken: 00:00:41.6837628
// *****************************************************
// RunChatCompletion
// *****************************************************
// Question: What is the capital of France? Who is that cities current mayor? What percentage of their life has been in the 21st century as of today?
// Result: The capital of France is Paris. The current mayor of Paris is Anne Hidalgo, who was born on June 19, 1959. As of today, she has lived for 64 years, with 23 of those years in the 21st century. Therefore, 35.94% of her life has been spent in the 21st century.
// Steps Taken: 14
// Skills Used: 12 (WebSearch.Search(8), time.Year(1), advancedCalculator.Calculator(3))
// Time Taken: 00:02:06.6682909
// *****************************************************
// RunTextCompletion
// *****************************************************
// Question: What is the current day of the calendar year? Using that as an angle in degrees, what is the area of a unit circle with that angle?
// Result: The current day of the calendar year is 177. The angle in degrees corresponding to this day is 174.6. The area of a unit circle with that angle is 0.764 * pi.
// Steps Taken: 16
// Skills Used: 2 (time.DayOfYear(1), time.Date(1))
// Time Taken: 00:01:29.9931039
// *****************************************************
// RunChatCompletion
// *****************************************************
// Question: What is the current day of the calendar year? Using that as an angle in degrees, what is the area of a unit circle with that angle?
// Result: The current day of the year is 177. Using that as an angle in degrees (approximately 174.58), the area of a unit circle with that angle is approximately 1.523 square units.
// Steps Taken: 11
// Skills Used: 9 (time.Now(1), time.DayOfYear(1), time.DaysBetween(1), time.MonthNumber(1), time.Day(1), advancedCalculator.Calculator(4))
// Time Taken: 00:01:41.5585861
// *****************************************************
