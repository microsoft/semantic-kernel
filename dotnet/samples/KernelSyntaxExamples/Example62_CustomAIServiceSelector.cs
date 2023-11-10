// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.ML.Tokenizers;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;
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

        KernelBuilder kernelBuilder = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletionService(
                deploymentName: azureDeploymentName,
                endpoint: azureEndpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: azureApiKey)
            .WithOpenAIChatCompletionService(
                modelId: openAIModelId,
                serviceId: "OpenAIChat",
                apiKey: openAIApiKey);

        await RunWithRequestSettingsAsync(kernelBuilder, "Hello AI, what can you do for me?");
        await RunWithRequestSettingsAsync(kernelBuilder, "Hello AI, provide an indepth description of what can you do for me as a bulleted list?");
        await RunWithGpt3xAsync(kernelBuilder, "Hello AI, what can you do for me?");
    }

    public static async Task RunWithRequestSettingsAsync(KernelBuilder kernelBuilder, string prompt)
    {
        Console.WriteLine($"======== With Request Settings: {prompt} ========");

        var kernel = kernelBuilder.WithAIServiceSelector(new TokenCountAIServiceSelector()).Build();

        var modelSettings = new List<AIRequestSettings>
        {
            new OpenAIRequestSettings() { ServiceId = "AzureOpenAIChat", MaxTokens = 400 },
            new OpenAIRequestSettings() { ServiceId = "OpenAIChat", MaxTokens = 200 }
        };
        var promptTemplateConfig = new PromptTemplateConfig() { ModelSettings = modelSettings };

        var skfunction = kernel.RegisterSemanticFunction(
            "MyFunction",
            prompt,
            promptTemplateConfig);

        var result = await kernel.RunAsync(skfunction);
        Console.WriteLine(result.GetValue<string>());
    }

    public static async Task RunWithGpt3xAsync(KernelBuilder kernelBuilder, string prompt)
    {
        Console.WriteLine($"======== Without GPT3x: {prompt} ========");

        var kernel = kernelBuilder.WithAIServiceSelector(new Gpt3xAIServiceSelector()).Build();

        var promptTemplateConfig = new PromptTemplateConfig();

        var skfunction = kernel.RegisterSemanticFunction(
            "MyFunction",
            prompt,
            promptTemplateConfig);

        var result = await kernel.RunAsync(skfunction);
        Console.WriteLine(result.GetValue<string>());
    }
}

public class TokenCountAIServiceSelector : IAIServiceSelector
{
    private readonly int _defaultMaxTokens = 300;
    private readonly int _minResponseTokens = 150;

    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        if (modelSettings is not null)
        {
            var tokens = this.CountTokens(renderedPrompt);

            int fewestTokens = 0;
            string? serviceId = null;
            AIRequestSettings? requestSettings = null;
            foreach (var model in modelSettings)
            {
                if (!string.IsNullOrEmpty(model.ServiceId))
                {
                    if (model is OpenAIRequestSettings openAIModel)
                    {
                        var responseTokens = (openAIModel.MaxTokens ?? this._defaultMaxTokens) - tokens;
                        if (serviceId is null || (responseTokens > this._minResponseTokens && responseTokens < fewestTokens))
                        {
                            fewestTokens = responseTokens;
                            serviceId = model.ServiceId;
                            requestSettings = model;
                        }
                    }
                }
            }
            Console.WriteLine($"Prompt tokens: {tokens}, Response tokens: {fewestTokens}");

            if (serviceId is not null)
            {
                Console.WriteLine($"Selected service: {serviceId}");
                var service = serviceProvider.GetService<T>(serviceId);
                if (service is not null)
                {
                    return (service, requestSettings);
                }
            }
        }

        throw new SKException("Unable to find AI service to handled request.");
    }

    /// <summary>
    /// MicrosoftML token counter implementation.
    /// </summary>
    private int CountTokens(string input)
    {
        Tokenizer tokenizer = new(new Bpe());
        var tokens = tokenizer.Encode(input).Tokens;

        return tokens.Count;
    }
}

public class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        var services = serviceProvider.GetServices<T>();
        foreach (var service in services)
        {
            var serviceModelId = service.GetModelId();
            if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine($"Selected model: {serviceModelId}");
                return (service, new OpenAIRequestSettings());
            }
        }

        throw new SKException("Unable to find AI service for GPT 3.x.");
    }
}
