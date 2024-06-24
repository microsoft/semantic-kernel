// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// This example shows how to use multiple prompt template formats.
public class Example64_MultiplePromptTemplates : BaseTest
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("semantic-kernel", "Hello AI, my name is {{$name}}. What is the origin of my name?")]
    [InlineData("handlebars", "Hello AI, my name is {{name}}. What is the origin of my name?")]
    public Task RunAsync(string templateFormat, string prompt)
    {
        WriteLine("======== Example64_MultiplePromptTemplates ========");

        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        var promptTemplateFactory = new AggregatorPromptTemplateFactory(
            new KernelPromptTemplateFactory(),
            new HandlebarsPromptTemplateFactory());

        return RunPromptAsync(kernel, prompt, templateFormat, promptTemplateFactory);
    }

    private async Task RunPromptAsync(Kernel kernel, string prompt, string templateFormat, IPromptTemplateFactory promptTemplateFactory)
    {
        WriteLine($"======== {templateFormat} : {prompt} ========");

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
        WriteLine(result.GetValue<string>());
    }

    public Example64_MultiplePromptTemplates(ITestOutputHelper output) : base(output)
    {
    }
}
