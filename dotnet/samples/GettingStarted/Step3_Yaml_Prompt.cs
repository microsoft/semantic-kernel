// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Resources;

namespace GettingStarted;

/// <summary>
/// This example shows how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
/// </summary>
public sealed class Step3_Yaml_Prompt(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
    /// </summary>
    [Fact]
    public async Task CreatePromptFromYaml()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Load prompt from resource
        var generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        var function = kernel.CreateFunctionFromPromptYaml(generateStoryYaml);

        // Invoke the prompt function and display the result
        Console.WriteLine(await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Dog" },
                { "length", "3" },
            }));

        // Load prompt from resource
        var generateStoryHandlebarsYaml = EmbeddedResource.Read("GenerateStoryHandlebars.yaml");
        function = kernel.CreateFunctionFromPromptYaml(generateStoryHandlebarsYaml, new HandlebarsPromptTemplateFactory());

        // Invoke the prompt function and display the result
        Console.WriteLine(await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Cat" },
                { "length", "3" },
            }));
    }
}
