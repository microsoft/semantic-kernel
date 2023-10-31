// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example61_MultipleLLMs
{
    /// <summary>
    /// Show how to run a semantic function and specify a specific service to use.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example61_MultipleLLMs ========");

        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId == null || openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .WithOpenAIChatCompletionService(
                modelId: openAIModelId,
                serviceId: "OpenAIChat",
                apiKey: openAIApiKey)
            .Build();

        await RunSemanticFunctionAsync(kernel, "AzureOpenAIChat");
        await RunSemanticFunctionAsync(kernel, "OpenAIChat");
    }

    public static async Task RunSemanticFunctionAsync(IKernel kernel, string serviceId)
    {
        Console.WriteLine($"======== {serviceId} ========");

        var prompt = "Hello AI, what can you do for me?";

        var result = await kernel.InvokeSemanticFunctionAsync(
           prompt,
           requestSettings: new AIRequestSettings()
           {
               ServiceId = serviceId
           });
        Console.WriteLine(result.GetValue<string>());
    }
}
