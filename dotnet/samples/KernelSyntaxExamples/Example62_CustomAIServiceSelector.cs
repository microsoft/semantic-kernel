// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example62_CustomAIServiceSelector
{
    /// <summary>
    /// Show how to configure model request settings
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example62_CustomAIServiceSelector ========");

        string azureApiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string azureDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string azureModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string azureEndpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (azureApiKey == null || azureDeploymentName == null || azureModelId == null || azureEndpoint == null)
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

        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletionService(
                deploymentName: azureDeploymentName,
                endpoint: azureEndpoint,
                serviceId: "AzureOpenAIChat",
                modelId: azureModelId,
                apiKey: azureApiKey,
                setAsDefault: true)
            .WithOpenAIChatCompletionService(
                modelId: openAIModelId,
                serviceId: "OpenAIChat",
                apiKey: openAIApiKey)
            // Use the custom AI service selector to select the GPT 3.x model
            .WithAIServiceSelector(new Gpt3xAIServiceSelector())
            .Build();

        var prompt = "Hello AI, what can you do for me?";
        var result = await kernel.InvokePromptAsync(prompt);
        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Custom AI service selector that selects the GPT 3.x model
    /// </summary>
    private sealed class Gpt3xAIServiceSelector : IAIServiceSelector
    {
        public (T?, AIRequestSettings?) SelectAIService<T>(Kernel kernel, SKContext context, KernelFunction function) where T : IAIService
        {
            var services = kernel.ServiceProvider.GetServices<T>();
            foreach (var service in services)
            {
                // Find the first service that has a model id that starts with "gpt-3"
                var serviceModelId = service.GetModelId();
                var endpoint = service.GetEndpoint();
                if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
                {
                    Console.WriteLine($"Selected model: {serviceModelId} {endpoint}");
                    return (service, new OpenAIRequestSettings());
                }
            }

            throw new SKException("Unable to find AI service for GPT 3.x.");
        }
    }
}
