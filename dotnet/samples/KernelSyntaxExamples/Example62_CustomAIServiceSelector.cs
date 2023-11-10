// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
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
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .WithOpenAIChatCompletionService(
                modelId: openAIModelId,
                serviceId: "OpenAIChat",
                apiKey: openAIApiKey)
            .WithAIServiceSelector(new ByModelIdAIServiceSelector(openAIModelId))
            .Build();

        var modelSettings = new List<AIRequestSettings>
        {
            new OpenAIRequestSettings() { ServiceId = "AzureOpenAIChat", ModelId = "" },
            new OpenAIRequestSettings() { ServiceId = "OpenAIChat", ModelId = openAIModelId }
        };

        await RunSemanticFunctionAsync(kernel, "Hello AI, what can you do for me?", modelSettings);
    }

    public static async Task RunSemanticFunctionAsync(IKernel kernel, string prompt, List<AIRequestSettings> modelSettings)
    {
        Console.WriteLine($"======== {prompt} ========");

        var promptTemplateConfig = new PromptTemplateConfig() { ModelSettings = modelSettings };

        var skfunction = kernel.RegisterSemanticFunction(
            "MyFunction",
            prompt,
            promptTemplateConfig);

        var result = await kernel.RunAsync(skfunction);
        Console.WriteLine(result.GetValue<string>());
    }
}

public class ByModelIdAIServiceSelector : IAIServiceSelector
{
    private readonly string _openAIModelId;

    public ByModelIdAIServiceSelector(string openAIModelId)
    {
        this._openAIModelId = openAIModelId;
    }

    public (T?, AIRequestSettings?) SelectAIService<T>(SKContext context, ISKFunction skfunction) where T : IAIService
    {
        foreach (var model in skfunction.ModelSettings)
        {
            if (model is OpenAIRequestSettings openAIModel)
            {
                if (openAIModel.ModelId == this._openAIModelId)
                {
                    var service = context.ServiceProvider.GetService<T>(openAIModel.ServiceId);
                    if (service is not null)
                    {
                        Console.WriteLine($"======== Selected service: {openAIModel.ServiceId} {openAIModel.ModelId} ========");
                        return (service, model);
                    }
                }
            }
        }

        throw new SKException("Unable to find AI service to handled request.");
    }
}
