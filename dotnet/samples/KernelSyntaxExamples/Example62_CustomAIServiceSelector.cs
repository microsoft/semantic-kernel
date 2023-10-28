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
        Console.WriteLine("======== Example61_CustomAIServiceSelector ========");

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
            .WithAIServiceSelector(new MyAIServiceSelector())
            .Build();

        var modelSettings = new List<AIRequestSettings>
        {
            new OpenAIRequestSettings() { ServiceId = "AzureOpenAIChat", MaxTokens = 400 },
            new OpenAIRequestSettings() { ServiceId = "OpenAIChat", MaxTokens = 200 }
        };

        await RunSemanticFunctionAsync(kernel, "Hello AI, what can you do for me?", modelSettings);
        await RunSemanticFunctionAsync(kernel, "Hello AI, provide an indepth description of what can you do for me as a bulleted list?", modelSettings);
    }

    public static async Task RunSemanticFunctionAsync(IKernel kernel, string prompt, List<AIRequestSettings> modelSettings)
    {
        Console.WriteLine($"======== {prompt} ========");

        var promptTemplateConfig = new PromptTemplateConfig() { ModelSettings = modelSettings };
        var promptTemplate = new PromptTemplate(prompt, promptTemplateConfig, kernel);

        var skfunction = kernel.RegisterSemanticFunction(
            "MyFunction",
            promptTemplateConfig,
            promptTemplate);

        var result = await kernel.RunAsync(skfunction);
        Console.WriteLine(result.GetValue<string>());
    }
}

public class MyAIServiceSelector : IAIServiceSelector
{
    private readonly int _defaultMaxTokens = 300;
    private readonly int _minResponseTokens = 150;

    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        if (modelSettings is null || modelSettings.Count == 0)
        {
            var service = serviceProvider.GetService<T>(null);
            if (service is not null)
            {
                return (service, null);
            }
        }
        else
        {
            var tokens = this.CountTokens(renderedPrompt);

            string? serviceId = null;
            int fewestTokens = 0;
            AIRequestSettings? requestSettings = null;
            AIRequestSettings? defaultRequestSettings = null;
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
                else
                {
                    // First request settings with empty or null service id is the default
                    defaultRequestSettings ??= model;
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

            if (defaultRequestSettings is not null)
            {
                var service = serviceProvider.GetService<T>(null);
                if (service is not null)
                {
                    return (service, defaultRequestSettings);
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
