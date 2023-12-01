// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;
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

        Kernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .Build();

        var promptTemplateFactory = new AggregatorPromptTemplateFactory(
            new KernelPromptTemplateFactory(),
            new HandlebarsPromptTemplateFactory());

        var skPrompt = "Hello AI, my name is {{$name}}. What is the origin of my name?";
        var handlebarsPrompt = "Hello AI, my name is {{name}}. What is the origin of my name?";

        await RunPromptAsync(kernel, skPrompt, "semantic-kernel", promptTemplateFactory);
        await RunPromptAsync(kernel, handlebarsPrompt, "handlebars", promptTemplateFactory);
    }

    public static async Task RunPromptAsync(Kernel kernel, string prompt, string templateFormat, IPromptTemplateFactory promptTemplateFactory)
    {
        Console.WriteLine($"======== {templateFormat} : {prompt} ========");

        var function = kernel.CreateFunctionFromPrompt(
            promptConfig: new PromptTemplateConfig()
            {
                Template = prompt,
                TemplateFormat = templateFormat,
                Name = "MyFunction",
            },
            promptTemplateFactory: promptTemplateFactory
        );

        var arguments = new KernelArguments()
        {
            { "name", "Bob" }
        };

        var result = await kernel.InvokeAsync(function, arguments);
        Console.WriteLine(result.GetValue<string>());
    }
}
