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

        string azureApiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string azureDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string azureModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string azureEndpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (azureApiKey == null || azureDeploymentName == null || azureEndpoint == null)
        {
            Console.WriteLine("AzureOpenAI endpoint, apiKey, or deploymentName not found. Skipping example.");
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
            .WithAzureOpenAIChatCompletionService(
                deploymentName: azureDeploymentName,
                endpoint: azureEndpoint,
                serviceId: "AzureOpenAIChat",
                modelId: azureModelId,
                apiKey: azureApiKey)
            .WithOpenAIChatCompletionService(
                modelId: openAIModelId,
                serviceId: "OpenAIChat",
                apiKey: openAIApiKey)
            .Build();

        //await RunByServiceIdAsync(kernel, "AzureOpenAIChat");
        //await RunByServiceIdAsync(kernel, "OpenAIChat");
        await RunByModelIdAsync(kernel, azureModelId);
        await RunByModelIdAsync(kernel, openAIModelId);
    }

    public static async Task RunByServiceIdAsync(IKernel kernel, string serviceId)
    {
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        var prompt = "Hello AI, what can you do for me?";

        var result = await kernel.InvokeSemanticFunctionAsync(
           prompt,
           requestSettings: new AIRequestSettings()
           {
               ServiceId = serviceId
           });
        Console.WriteLine(result.GetValue<string>());
    }

    public static async Task RunByModelIdAsync(IKernel kernel, string modelId)
    {
        Console.WriteLine($"======== Model Id: {modelId} ========");

        var prompt = "Hello AI, what can you do for me?";

        var result = await kernel.InvokeSemanticFunctionAsync(
           prompt,
           requestSettings: new AIRequestSettings()
           {
               ModelId = modelId
           });
        Console.WriteLine(result.GetValue<string>());
    }
}
