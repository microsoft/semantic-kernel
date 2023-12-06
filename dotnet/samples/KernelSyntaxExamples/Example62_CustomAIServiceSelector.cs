// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Services;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example62_CustomAIServiceSelector
{
    /// <summary>
    /// Show how to use a custom AI service selector to select a specific model
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
            Console.WriteLine("AzureOpenAI endpoint, apiKey, deploymentName or modelId not found. Skipping example.");
            return;
        }

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId == null || openAIApiKey == null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        // Build a kernel with multiple chat completion services
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletion(
                deploymentName: azureDeploymentName,
                endpoint: azureEndpoint,
                serviceId: "AzureOpenAIChat",
                modelId: azureModelId,
                apiKey: azureApiKey)
            .WithOpenAIChatCompletion(
                modelId: openAIModelId,
                serviceId: "OpenAIChat",
                apiKey: openAIApiKey)
            // Use custom AI service selector to select the GPT model
            .WithAIServiceSelector(new GptAIServiceSelector())
            .Build();

        // This invocation is done with the model selected by the custom selector
        var prompt = "Hello AI, what can you do for me?";
        var result = await kernel.InvokePromptAsync(prompt);
        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Custom AI service selector that selects a GPT model.
    /// This selector just naively selects the first service that provides
    /// a completion model whose name starts with "gpt". But this logic could
    /// be as elaborate as needed to apply your own selection criteria.
    /// </summary>
    private sealed class GptAIServiceSelector : IAIServiceSelector
    {
        public (T?, PromptExecutionSettings?) SelectAIService<T>(Kernel kernel, KernelFunction function, KernelArguments arguments) where T : class, IAIService
        {
            foreach (var service in kernel.GetAllServices<T>())
            {
                // Find the first service that has a model id that starts with "gpt"
                var serviceModelId = service.GetModelId();
                var endpoint = service.GetEndpoint();
                if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt", StringComparison.OrdinalIgnoreCase))
                {
                    Console.WriteLine($"Selected model: {serviceModelId} {endpoint}");
                    return (service, new OpenAIPromptExecutionSettings());
                }
            }

            throw new KernelException("Unable to find AI service for GPT");
        }
    }
}
