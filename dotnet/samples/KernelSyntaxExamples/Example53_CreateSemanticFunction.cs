// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SemanticFunctions;
using static Microsoft.SemanticKernel.SemanticFunctions.PromptConfig;

// ReSharper disable once InconsistentNaming
public static class Example53_CreateSemanticFunction
{
    public static async Task RunAsync()
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string deploymentName = TestConfiguration.AzureOpenAI.DeploymentName;

        var promptRequestSettings = new PromptRequestSettings();
        promptRequestSettings.Properties["temperature"] = 0.9;
        promptRequestSettings.Properties["max_tokens"] = 1024;

        var promptConfig = new PromptConfig()
        {
            Description = "Say hello in German",
            InputParameters = new(),
            PluginName = "SpeakGermanPlugin",
            FunctionName = "SayHello",
            Template = "Say hello in German",
            RequestSettings = new List<PromptRequestSettings>() { promptRequestSettings },
        };

        IKernel kernel = Kernel.Builder
            .WithAzureTextCompletionService(deploymentName: deploymentName, endpoint: endpoint, apiKey: apiKey)
            .Build();

        var function = kernel.CreateSemanticFunction(promptConfig);

        var response = await kernel.RunAsync(function);

        Console.WriteLine(response.Result);
    }
}
