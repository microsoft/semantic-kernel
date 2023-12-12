// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;

/**
 * This example shows how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
 */
// ReSharper disable once InconsistentNaming
public static class Step3_Yaml_Prompt
{
    /// <summary>
    /// Show how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
    /// </summary>
    public static async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Load prompt from resource
        var resourceName = "Resources.GenerateStory.yaml";
        using StreamReader reader1 = new(Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName)!);
        var function = kernel.CreateFunctionFromPromptYaml(await reader1.ReadToEndAsync());

        // Invoke the prompt function and display the result
        Console.WriteLine(await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Dog" },
                { "length", "3" },
            }));

        // Load prompt from resource
        resourceName = "Resources.GenerateStoryHandlebars.yaml";
        using StreamReader reader2 = new(Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName)!);
        function = kernel.CreateFunctionFromPromptYaml(await reader2.ReadToEndAsync(), new HandlebarsPromptTemplateFactory());

        // Invoke the prompt function and display the result
        Console.WriteLine(await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Dog" },
                { "length", "3" },
            }));
    }
}
