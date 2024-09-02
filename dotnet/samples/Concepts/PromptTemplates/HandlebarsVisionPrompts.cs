// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace PromptTemplates;

// This example shows how to use chat completion handlebars template prompts with base64 encoded images as a parameter.
public class HandlebarsVisionPrompts(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        const string HandlebarsTemplate = """
            <message role="system">You are an AI assistant designed to help with image recognition tasks.</message>
            <message role="user">
               <text>{{request}}</text>
               <image>{{imageData}}</image>
            </message>
            """;

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var templateFactory = new HandlebarsPromptTemplateFactory();
        var promptTemplateConfig = new PromptTemplateConfig()
        {
            Template = HandlebarsTemplate,
            TemplateFormat = "handlebars",
            Name = "Vision_Chat_Prompt",
        };
        var function = kernel.CreateFunctionFromPrompt(promptTemplateConfig, templateFactory);

        var arguments = new KernelArguments(new Dictionary<string, object?>
        {
            {"request","Describe this image:"},
            {"imageData", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAACVJREFUKFNj/KTO/J+BCMA4iBUyQX1A0I10VAizCj1oMdyISyEAFoQbHwTcuS8AAAAASUVORK5CYII="}
        });

        var response = await kernel.InvokeAsync(function, arguments);
        Console.WriteLine(response);

        /*
        Output:
           The image is a solid block of bright red color. There are no additional features, shapes, or textures present.
        */
    }
}
