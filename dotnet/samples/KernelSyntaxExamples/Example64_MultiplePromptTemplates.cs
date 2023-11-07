// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine;
using RepoUtils;

namespace KernelSyntaxExamples;

/**
 * This example shows how to use multiple prompt template formats.
 */

// ReSharper disable once InconsistentNaming
public static class Example64_MultiplePromptTemplates
{
    /// <summary>
    /// Show how to run a semantic function and specify a specific service to use.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example64_MultiplePromptTemplates ========");

        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .Build();

    }

    public static async Task RunSemanticFunctionAsync(IKernel kernel, string prompt, string templateFormat, IPromptTemplateFactory promptTemplateFactory)
    {
        Console.WriteLine($"======== {templateFormat} ========");

        var skfunction = kernel.CreateSemanticFunction(
            promptTemplate: prompt,
            functionName: "MyFunction",
            promptTemplateConfig: new PromptTemplateConfig()
            {
                TemplateFormat = templateFormat
            },
            promptTemplateFactory: promptTemplateFactory
        );
        var result = await kernel.RunAsync(skfunction);
        Console.WriteLine(result.GetValue<string>());
    }
}
