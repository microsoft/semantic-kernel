// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using NCalcSkills;
using RepoUtils;

/**
 * This example shows how to use Stepwise Planner to create a plan for a given goal.
 */

// ReSharper disable once InconsistentNaming
public static class Example48_StepwisePlanner
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

    // RunTextCompletion
    // *****************************************************
    // Question: Who is the current president of the United States? What is his current age divided by 2
    // Result: The current president of the United States is Joe Biden. His current age divided by 2 is 40.
    // Steps Taken: 6
    // Skills Used: 5 (WebSearch.Search(1), time.Year(1), time.MonthNumber(1), advancedCalculator.Calculator(2))
    // Time Taken: 00:00:29.7883820
    // *****************************************************
    // RunChatCompletion
    // *****************************************************
    // Question: Who is the current president of the United States? What is his current age divided by 2
    // Result: The current president of the United States is Joseph R. Biden, Jr. His current age divided by 2 is 40.5.
    // Steps Taken: 8
    // Skills Used: 7 (WebSearch.Search(4), time.Year(1), advancedCalculator.Calculator(2))
    // Time Taken: 00:03:13.8966442
    // *****************************************************

    // RunTextCompletion
    // *****************************************************
    // Question: Who is Leo DiCaprio's girlfriend? What is her current age raised to the (his current age)/100 power?
    // Result: Leo DiCaprio's girlfriend is Camila Morrone, and her current age raised to the (his current age)/100 power is 5.
    // Steps Taken: 26
    // Skills Used: 13 (WebSearch.Search(4), time.Year(1), time.MonthNumber(2), time.Day(1), store(2), advancedCalculator.Calculator(3))
    // Time Taken: 00:01:49.6237232
    // *****************************************************

    // RunTextCompletion
    // *****************************************************
    // Question: What is the capital of France? Who is that cities current mayor? What percentage of their life has been in the 21st century as of today?
    // Result: The capital of France is Paris. The current mayor of Paris is Anne Hidalgo. The percentage of her life that has been in the 21st century as of today is 36.64%.
    // Steps Taken: 10
    // Skills Used: 8 (WebSearch.Search(3), time.Today(1), advancedCalculator.Calculator(4))
    // Time Taken: 00:00:56.3130173
    // *****************************************************

    // RunTextCompletion
    // *****************************************************
    // Question: What is the current day of the calendar year? Using that as an angle in degrees, what is the area of a unit circle with that angle?
    // Result: The area of a sector of a unit circle with the angle corresponding to the current day of the calendar year is 1.4022465753424658 square units.
    // Steps Taken: 5
    // Skills Used: 4 (time.DayOfYear(1), WebSearch.Search(1), advancedCalculator.Calculator(2))
    // Time Taken: 00:00:31.5772418
    // *****************************************************

    public static async Task RunTextCompletion(string question)
    {
        Console.WriteLine("RunTextCompletion");
        var kernel = GetKernel();
        await RunWithQuestion(kernel, question);
    }

    public static async Task RunChatCompletion(string question)
    {
        Console.WriteLine("RunChatCompletion");
        var kernel = GetKernel(true);
        await RunWithQuestion(kernel, question);
    }

    public static async Task RunWithQuestion(IKernel kernel, string question)
    {
        using var bingConnector = new BingConnector(Env.Var("BING_API_KEY"));
        var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);

        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "advancedCalculator");
        // kernel.ImportSkill(new SimpleCalculatorSkill(kernel), "basicCalculator");
        kernel.ImportSkill(new TimeSkill(), "time");

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        Console.WriteLine("Question: " + question);

        var config = new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig();
        config.ExcludedFunctions.Add("TranslateMathProblem");
        config.MinIterationTimeMs = 2500;
        config.MaxTokens = 4000;

        StepwisePlanner planner = new(kernel, config);
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
                Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_ENDPOINT"),
                Env.Var("AZURE_OPENAI_KEY"),
                alsoAsTextCompletion: true,
                setAsDefault: true);
        }
        else
        {
            builder.WithAzureTextCompletionService(
                Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_ENDPOINT"),
                Env.Var("AZURE_OPENAI_KEY"));
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

// *****************************************************
// Goal :Who is Leo DiCaprio's girlfriend? What is her current age raised to the 0.43 power?
// *****************************************************
// 01:54:27 Observation : Sarah Stier // Getty Images March 2021: They enjoy a beachside getaway. DiCaprio and Morrone headed to Malibu with friends for brief holiday. The actress shared photos from their trip to...
// 01:54:32 Observation : Michele Morrone ( Italian pronunciation: [mi'k??le mor'ro?ne]; born 3 October 1990) is an Italian actor, model, singer, and fashion designer appearing in both Italian and Polish films. He gained international recognition after portraying the role of Massimo Torricelli in the 2020 erotic romantic drama 365 Days . Early life
// 01:54:37 Observation : Camila Rebeca Morrone Polak [3] (born June 16, 1997) [4] is an American model and actress. She made her acting debut in the James Franco film Bukowski and subsequently appeared in the films Death Wish and Never Goin' Back, both premiering at the Sundance Film Festival in January 2018. Early life and education
// 01:54:44 Observation : Answer:3.9218486893172186
// *****************************************************
// Result :Leo DiCaprio's girlfriend is Camila Morrone and her current age raised to the 0.43 power is 3.92.
// Steps Taken: 5
// *****************************************************
// *****************************************************
// Goal :Who is the current president of the United States? What is his current age divided by 2
// *****************************************************
// 01:54:52 Observation : U.S. facts and figures Presidents, vice presidents, and first ladies Presidents, vice presidents, and first ladies Learn about the duties of president, vice president, and first lady of the United States. Find out how to contact and learn more about current and past leaders. President of the United States Vice president of the United States
// 01:55:00 Observation : On January 20, 2021, at the age of 78, Biden became the oldest president in U.S. history, the first to have a female vice president, and the first from Delaware. ... : 411-414, 419 Obama campaign staffers called Biden's blunders "Joe bombs" and kept Biden uninformed about strategy discussions, which in turn irked Biden. Relations between the ...
// 01:55:04 Observation : Answer:39
// *****************************************************
// Result :The current president of the United States is Joe Biden, and his current age divided by 2 is 39.
// Steps Taken: 4
// *****************************************************
// *****************************************************
// Goal :What is the capital of France? Who is that cities current mayor? What percentage of their life has been in the 21st century as of today?
// *****************************************************
// 01:55:13 Observation : Paris is the capital of what country? Paris; Eiffel Tower
// 01:55:24 Observation : Early life and education [ edit] Family background and youth [ edit] Hidalgo was born in San Fernando, province of Cádiz, Spain. [1] Her paternal grandfather was a Spanish Socialist who became a refugee in France after the end of the Spanish Civil War along with his wife and his four children.
// 01:55:28 Observation : Friday, June 2, 2023 1:55 PM
// 01:55:41 Observation : Answer:35.9375
// *****************************************************
// Result :The capital of France is Paris. The current mayor of Paris is Anne Hidalgo. As of 2023, 35.9375 percent of her life has been in the 21st century.
// Steps Taken: 8
// *****************************************************
// *****************************************************
// Goal :What is the current day of the calendar year? Using that as an angle in degrees, what is the area of a unit circle with that angle?
// *****************************************************
// 10:51:27 warn: object[0] Observation : Error invoking action time.DayOfYear : Unknown error (UnknownError): The function 'time.DayOfYear' was not found.
// 10:51:36 warn: object[0] Observation : 05
// 10:51:38 warn: object[0] Observation : 06
// 10:51:50 warn: object[0] Observation : 2023
// 10:52:02 warn: object[0] Observation : Answer:3
// 10:53:06 warn: object[0] Observation : Answer:1.361356816555577
// *****************************************************
// Result :The area of the sector of the unit circle with the angle of 156 degrees is 1.36 square units.
// Steps Taken: 24
// Skills Used: Total Skills Called: 6 (time.DayOfYear(1), time.Day(1), time.MonthNumber(1), time.Year(1), calculator.Calculator(2))
// *****************************************************
// == DONE ==
