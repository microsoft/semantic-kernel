// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using NCalcPlugins;
using RepoUtils;

/**
 * This example shows how to use Stepwise Planner to create and run a stepwise plan for a given goal.
 */

// ReSharper disable once InconsistentNaming
public static class Example51_StepwisePlanner
{
    // Used to override the max allowed tokens when running the plan
    internal static int? ChatMaxTokens = null;
    internal static int? TextMaxTokens = null;

    // Used to quickly modify the chat model used by the planner
    internal static string? ChatModelOverride = null; //"gpt-35-turbo";
    internal static string? TextModelOverride = null; //"text-davinci-003";

    internal static string? Suffix = null;

    public static async Task RunAsync()
    {
        string[] questions = new string[]
        {
            "What color is the sky?",
            "What is the weather in Seattle?",
            "What is the tallest mountain on Earth? How tall is it divided by 2?",
            "What is the capital of France? Who is that city's current mayor? What percentage of their life has been in the 21st century as of today?",
            "What is the current day of the calendar year? Using that as an angle in degrees, what is the area of a unit circle with that angle?",
            "If a spacecraft travels at 0.99 the speed of light and embarks on a journey to the nearest star system, Alpha Centauri, which is approximately 4.37 light-years away, how much time would pass on Earth during the spacecraft's voyage?"
        };

        foreach (var question in questions)
        {
            for (int i = 0; i < 1; i++)
            {
                await RunTextCompletion(question);
                await RunChatCompletion(question);
            }
        }

        PrintResults();
    }

    // print out summary table of ExecutionResults
    private static void PrintResults()
    {
        Console.WriteLine("**************************");
        Console.WriteLine("Execution Results Summary:");
        Console.WriteLine("**************************");

        foreach (var question in ExecutionResults.Select(s => s.question).Distinct())
        {
            Console.WriteLine("Question: " + question);
            Console.WriteLine("Mode\tModel\tAnswer\tStepsTaken\tIterations\tTimeTaken");
            foreach (var er in ExecutionResults.OrderByDescending(s => s.model).Where(s => s.question == question))
            {
                Console.WriteLine($"{er.mode}\t{er.model}\t{er.stepsTaken}\t{er.iterations}\t{er.timeTaken}\t{er.answer}");
            }
        }
    }

    private struct ExecutionResult
    {
        public string mode;
        public string? model;
        public string? question;
        public string? answer;
        public string? stepsTaken;
        public string? iterations;
        public string? timeTaken;
    }

    private static List<ExecutionResult> ExecutionResults = new();

    private static async Task RunTextCompletion(string question)
    {
        Console.WriteLine("RunTextCompletion");
        ExecutionResult currentExecutionResult = default;
        currentExecutionResult.mode = "RunTextCompletion";
        var kernel = GetKernel(ref currentExecutionResult);
        await RunWithQuestion(kernel, currentExecutionResult, question, TextMaxTokens);
    }

    private static async Task RunChatCompletion(string question, string? model = null)
    {
        Console.WriteLine("RunChatCompletion");
        ExecutionResult currentExecutionResult = default;
        currentExecutionResult.mode = "RunChatCompletion";
        var kernel = GetKernel(ref currentExecutionResult, true, model);
        await RunWithQuestion(kernel, currentExecutionResult, question, ChatMaxTokens);
    }

    private static async Task RunWithQuestion(IKernel kernel, ExecutionResult currentExecutionResult, string question, int? MaxTokens = null)
    {
        currentExecutionResult.question = question;
        var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        var webSearchEngineSkill = new WebSearchEnginePlugin(bingConnector);

        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        kernel.ImportSkill(new LanguageCalculatorPlugin(kernel), "semanticCalculator");
        kernel.ImportSkill(new TimePlugin(), "time");

        // StepwisePlanner is instructed to depend on available functions.
        // We expose this function to increase the flexibility in it's ability to answer
        // given the relatively small number of functions we have in this example.
        // This seems to be particularly helpful in these examples with gpt-35-turbo -- even though it
        // does not *use* this function. It seems to help the planner find a better path to the answer.
        kernel.CreateSemanticFunction(
            "Generate an answer for the following question: {{$input}}",
            functionName: "GetAnswerForQuestion",
            skillName: "AnswerBot",
            description: "Given a question, get an answer and return it as the result of the function");

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        Console.WriteLine("Question: " + question);

        var plannerConfig = new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig();
        plannerConfig.ExcludedFunctions.Add("TranslateMathProblem");
        plannerConfig.ExcludedFunctions.Add("DaysAgo");
        plannerConfig.ExcludedFunctions.Add("DateMatchingLastDayName");
        plannerConfig.MinIterationTimeMs = 1500;
        plannerConfig.MaxIterations = 25;

        if (!string.IsNullOrEmpty(Suffix))
        {
            plannerConfig.Suffix = $"{Suffix}\n{plannerConfig.Suffix}";
            currentExecutionResult.question = $"[Assisted] - {question}";
        }

        if (MaxTokens.HasValue)
        {
            plannerConfig.MaxTokens = MaxTokens.Value;
        }

        SKContext result;
        sw.Start();

        try
        {
            StepwisePlanner planner = new(kernel: kernel, config: plannerConfig);
            var plan = planner.CreatePlan(question);

            result = await kernel.RunAsync(plan);

            if (result.Result.Contains("Result not found, review _stepsTaken to see what", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine("Could not answer question in " + plannerConfig.MaxIterations + " iterations");
                currentExecutionResult.answer = "Could not answer question in " + plannerConfig.MaxIterations + " iterations";
            }
            else
            {
                Console.WriteLine("Result: " + result.Result);
                currentExecutionResult.answer = result.Result;
            }

            if (result.Variables.TryGetValue("stepCount", out string? stepCount))
            {
                Console.WriteLine("Steps Taken: " + stepCount);
                currentExecutionResult.stepsTaken = stepCount;
            }

            if (result.Variables.TryGetValue("skillCount", out string? skillCount))
            {
                Console.WriteLine("Skills Used: " + skillCount);
            }

            if (result.Variables.TryGetValue("iterations", out string? iterations))
            {
                Console.WriteLine("Iterations: " + iterations);
                currentExecutionResult.iterations = iterations;
            }
        }
#pragma warning disable CA1031
        catch (Exception ex)
        {
            Console.WriteLine("Exception: " + ex);
        }

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        currentExecutionResult.timeTaken = sw.Elapsed.ToString();
        ExecutionResults.Add(currentExecutionResult);
        Console.WriteLine("*****************************************************");
    }

    private static IKernel GetKernel(ref ExecutionResult result, bool useChat = false, string? model = null)
    {
        var builder = new KernelBuilder();
        var maxTokens = 0;
        if (useChat)
        {
            builder.WithAzureChatCompletionService(
                model ?? ChatModelOverride ?? TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey,
                alsoAsTextCompletion: true,
                setAsDefault: true);

            maxTokens = ChatMaxTokens ?? (new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig()).MaxTokens;
            result.model = model ?? ChatModelOverride ?? TestConfiguration.AzureOpenAI.ChatDeploymentName;
        }
        else
        {
            builder.WithAzureTextCompletionService(
                model ?? TextModelOverride ?? TestConfiguration.AzureOpenAI.DeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);

            maxTokens = TextMaxTokens ?? (new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig()).MaxTokens;
            result.model = model ?? TextModelOverride ?? TestConfiguration.AzureOpenAI.DeploymentName;
        }

        Console.WriteLine($"Model: {result.model} ({maxTokens})");

        var kernel = builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithRetryBasic(new()
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                MinRetryDelay = TimeSpan.FromSeconds(3),
            })
            .Build();

        return kernel;
    }
}
