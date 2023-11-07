// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Basic;
using Microsoft.SemanticKernel.TemplateEngine.Handlebars;
using RepoUtils;

/**
 * This example shows how to use multiple prompt template formats.
 */
// ReSharper disable once InconsistentNaming
public static class Example64_MultiplePromptTemplates
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
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
            .WithAzureOpenAIChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .Build();

        var promptTemplateFactory = new AggregatorPromptTemplateFactory(
            new BasicPromptTemplateFactory(),
            new HandlebarsPromptTemplateFactory());

        var skPrompt = "Hello AI, my name is {{$name}}. What is the origin of my name?";
        var handlebarsPrompt = "Hello AI, my name is {{name}}. What is the origin of my name?";

        await RunSemanticFunctionAsync(kernel, skPrompt, "semantic-kernel", promptTemplateFactory);
        await RunSemanticFunctionAsync(kernel, handlebarsPrompt, "handlebars", promptTemplateFactory);
    }

    public static async Task RunSemanticFunctionAsync(IKernel kernel, string prompt, string templateFormat, IPromptTemplateFactory promptTemplateFactory)
    {
        Console.WriteLine($"======== {templateFormat} : {prompt} ========");

        var skfunction = kernel.CreateSemanticFunction(
            promptTemplate: prompt,
            functionName: "MyFunction",
            promptTemplateConfig: new PromptTemplateConfig()
            {
                TemplateFormat = templateFormat
            },
            promptTemplateFactory: promptTemplateFactory
        );

        var variables = new ContextVariables()
        {
            { "name", "Bob" }
        };

        var result = await kernel.RunAsync(skfunction, variables);
        Console.WriteLine(result.GetValue<string>());
    }
}
