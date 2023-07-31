// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using NCalcSkills;
using RepoUtils;

/**
 * This example shows how to use Stepwise Planner to create a plan for a given goal.
 */

// ReSharper disable once InconsistentNaming
public static partial class Example00_01_PlayFabDataQnA
{
    public static async Task RunAsync()
    {
        string[] questions = new string[]
        {
            "How many players played my game yesterday?",
            "What is the average number of players I had last week excluding Friday and Monday?"
        };

        foreach (var question in questions)
        {
            await RunTextCompletion(question);
            // await RunChatCompletion(question);
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

        // kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        kernel.ImportSkill(new GameDataSearchSkill(), "GameDataSearch");
        kernel.ImportSkill(new CsvDataAnalyzerSkill(kernel), "CsvDataAnalyzer");

        kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "advancedCalculator");
        // kernel.ImportSkill(new SimpleCalculatorSkill(kernel), "basicCalculator");
        kernel.ImportSkill(new TimeSkill(), "time");

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        Console.WriteLine("Question: " + question);

        var plannerConfig = new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig();
        plannerConfig.ExcludedFunctions.Add("TranslateMathProblem");
        plannerConfig.MinIterationTimeMs = 1500;
        plannerConfig.MaxTokens = 2000;

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
            .WithLogger(ConsoleLogger.Logger)
            .WithAzureTextEmbeddingGenerationService(
                deploymentName: "text-embedding-ada-002",
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Configure(c => c.SetDefaultHttpRetryConfig(new HttpRetryConfig
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                MinRetryDelay = TimeSpan.FromSeconds(3),
            }))
            .Build();

        return kernel;
    }

    public class GameQnaSkill
    {
    }

    public class GameDataSearchSkill
    {
        [SKFunction, SKName("GameDataSearch"), Description("Useful for getting the relevant data of a game for a given question.")]
        public Task<string> SearchAsync(
            [Description("A question about a game for which data is needed.")]
            string input,
            SKContext context)
        {
            DateTime today = DateTime.UtcNow;
            string ret = $""""
            The Game Daily active users (DAU). Each row represents the number of unique users in that day:
            Date, DAU
            {today:yyyy/MM/dd}, 28000
            {today.AddDays(-1):yyyy/MM/dd}, 27000
            {today.AddDays(-2):yyyy/MM/dd}, 26000
            {today.AddDays(-3):yyyy/MM/dd}, 25000
            {today.AddDays(-4):yyyy/MM/dd}, 24000
            {today.AddDays(-5):yyyy/MM/dd}, 23000
            {today.AddDays(-6):yyyy/MM/dd}, 22000
            {today.AddDays(-7):yyyy/MM/dd}, 21000
            {today.AddDays(-8):yyyy/MM/dd}, 20000

            The Game Monthly active users (MAU). Each row represents the number of unique users in the last seven days.
            Date, MAU
            {today:yyyy/MM/dd}, 280000
            {today.AddDays(-1):yyyy/MM/dd}, 270000
            {today.AddDays(-2):yyyy/MM/dd}, 260000
            {today.AddDays(-3):yyyy/MM/dd}, 250000
            {today.AddDays(-4):yyyy/MM/dd}, 240000
            {today.AddDays(-5):yyyy/MM/dd}, 230000
            {today.AddDays(-6):yyyy/MM/dd}, 220000
            {today.AddDays(-7):yyyy/MM/dd}, 210000
            {today.AddDays(-8):yyyy/MM/dd}, 200000
            """";

            return Task.FromResult(ret);
        }
    }

    public class CsvDataAnalyzerSkill
    {
        private readonly IKernel _kernel;

        public CsvDataAnalyzerSkill(IKernel kernel)
        {
            _kernel = kernel ?? throw new ArgumentNullException(nameof(kernel));
        }

        [SKFunction, SKName("CsvDataAnalyzer"), Description("Useful for analyzing an input comma seperated (CSV) table and extract the answer for a given question regards that data.")]
        public async Task<string> AnalyzeAsync(
            [Description("A question that should be answered.")]
            string input,
            [Description("An input comma seperated CSV text data with the raw data needed for anwering the question.")]
            string csv,
            SKContext context)
        {
            DateTime today = DateTime.UtcNow;

            const string FunctionDefinition = @"
Generate python scripts that loads the comma-seperated (CSV) data inline (within the python script) to a dataframe.
Do not assume the CSV data is available in any external file
The script should then attempt to answer the provided question and print the output to console.
The script should not attempt to use panda module

[Question]
{{$input}}

[Input CSV]
{{$csv}}

[Result Python Script]
";

            var csvAnalyzeFunction = _kernel.CreateSemanticFunction(FunctionDefinition, maxTokens: 500, temperature: 0.1, topP: 1);

            var result = await csvAnalyzeFunction.InvokeAsync(context);

            // Path to the Python executable
            string pythonPath = "python"; // Use "python3" if on a Unix-like system

            // Inline Python script
            string pythonScript = result.Result.Replace('"', '\'');

            // Create a ProcessStartInfo and set the required properties
            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-c \"" + pythonScript + "\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            // Create a new Process
            using Process process = new() { StartInfo = startInfo };

            // Start the Python process
            process.Start();

            // Read the Python process output
            string output = process.StandardOutput.ReadToEnd().Trim();

            // Wait for the process to finish
            process.WaitForExit();

            return output;
        }
    }
}
