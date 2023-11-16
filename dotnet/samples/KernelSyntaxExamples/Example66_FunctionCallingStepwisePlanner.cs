// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planners;
using Microsoft.SemanticKernel.Plugins.Core;
using Plugins;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example66_FunctionCallingStepwisePlanner
{
    public static async Task RunAsync()
    {
        string[] questions = new string[]
        {
            "What is the current hour number, plus 5?",
            "What is 387 minus 22? Email the solution to John and Mary.",
            "Write a limerick, translate it to Spanish, and send it to Jane",
        };

        var kernel = InitializeKernel();

        var config = new FunctionCallingStepwisePlannerConfig
        {
            MaxIterations = 15,
            MaxTokens = 4000,
        };
        var planner = new FunctionCallingStepwisePlanner(kernel, config);

        foreach (var question in questions)
        {
            FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(question);
            Console.WriteLine($"Q: {question}\nA: {result.FinalAnswer}");

            // You can uncomment the line below to see the planner's process for completing the request.
            // Console.WriteLine($"Chat history:\n{result.ChatHistory?.AsJson()}");
        }
    }

    /// <summary>
    /// Initialize the kernel and load plugins.
    /// </summary>
    /// <returns>A kernel instance</returns>
    private static IKernel InitializeKernel()
    {
        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        kernel.ImportFunctions(new EmailPlugin(), "EmailPlugin");
        kernel.ImportFunctions(new MathPlugin(), "MathPlugin");
        kernel.ImportFunctions(new TimePlugin(), "TimePlugin");

        return kernel;
    }
}
