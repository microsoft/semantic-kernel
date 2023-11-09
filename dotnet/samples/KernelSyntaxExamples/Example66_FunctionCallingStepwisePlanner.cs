// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planners;
using Plugins;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example66_FunctionCallingStepwisePlanner
{
    internal static string? ChatModelOverride = null; //"gpt-35-turbo-0613"

    public static async Task RunAsync()
    {
        string[] questions = new string[]
        {
            "Write a limerick and send it via email to John"
        };

        var kernel = InitializeKernel();

        var config = new FunctionCallingStepwisePlannerConfig
        {

        };
        var planner = new FunctionCallingStepwisePlanner(kernel, config);

        foreach (var question in questions)
        {
            FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(question);
            Console.WriteLine($"Q: {question}\nA: {result.Message}");

            // You can examine `result.ChatHistory` to see the planner's process for completing the request.
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
                ChatModelOverride ?? TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        kernel.ImportFunctions(new EmailPlugin(), "EmailPlugin");

        return kernel;
    }
}
