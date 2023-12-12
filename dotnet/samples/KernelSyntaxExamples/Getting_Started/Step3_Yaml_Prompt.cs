// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;

/**
 * This example shows how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
 */
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
        var function = kernel.CreateFunctionFromPromptYaml(GenerateStoryYaml);

        // Invoke the prompt function and display the result
        Console.WriteLine(await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Dog" },
                { "length", "3" },
            }));

        // Load prompt from resource
        function = kernel.CreateFunctionFromPromptYaml(GenerateStoryHandlebarsYaml, new HandlebarsPromptTemplateFactory());

        // Invoke the prompt function and display the result
        Console.WriteLine(await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Cat" },
                { "length", "3" },
            }));
    }

    private const string GenerateStoryYaml = @"
name: GenerateStory
template: |
  Tell a story about {{$topic}} that is {{$length}} sentences long.
template_format: semantic-kernel
description: A function that generates a story about a topic.
input_variables:
  - name: topic
    description: The topic of the story.
    is_required: true
  - name: length
    description: The number of sentences in the story.
    is_required: true
output_variable:
  description: The generated story.
execution_settings:
  - temperature: 0.6
";

    private const string GenerateStoryHandlebarsYaml = @"
name: GenerateStory
template: |
  Tell a story about {{topic}} that is {{length}} sentences long.
template_format: handlebars
description: A function that generates a story about a topic.
input_variables:
  - name: topic
    description: The topic of the story.
    is_required: true
  - name: length
    description: The number of sentences in the story.
    is_required: true
output_variable:
  description: The generated story.
execution_settings:
  - model_id: gpt-4
    temperature: 0.6
  - model_id: gpt-3.5-turbo
    temperature: 0.4  
  - temperature: 0.5
";
}
