// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

// ReSharper disable once InconsistentNaming
/// <summary>
/// TODO: @chris
/// </summary>
public static class Example70_Assistant
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example70_Assistant ========");

        string apiKey = TestConfiguration.OpenAI.ApiKey;

        if (apiKey == null)
        {
            Console.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        //IKernel kernel = new KernelBuilder()
        //    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
        //    .WithAzureOpenAIChatCompletionService(
        //        deploymentName: chatDeploymentName,
        //        endpoint: endpoint,
        //        serviceId: "AzureOpenAIChat",
        //        apiKey: apiKey)
        //    .Build();

        await Task.Delay(0);
    }
}
