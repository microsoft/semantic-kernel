// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

// ReSharper disable once InconsistentNaming
/// <summary>
/// TODO: @chris
/// </summary>
public static class Example71_AssistantDelegation
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example71_AssistantDelegation ========");

        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, or deploymentName not found. Skipping example.");
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
