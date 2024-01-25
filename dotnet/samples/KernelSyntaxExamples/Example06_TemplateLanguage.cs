// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example06_TemplateLanguage : BaseTest
{
    /// <summary>
    /// Show how to invoke a Method Function written in C#
    /// from a Prompt Function written in natural language
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("======== TemplateLanguage ========");

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId == null || openAIApiKey == null)
        {
            this.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        // Functions loaded here are available as "time.*"
        kernel.ImportPluginFromType<TimePlugin>("time");

        // Prompt Function invoking time.Date and time.Time method functions
        const string FunctionDefinition = @"
Today is: {{time.Date}}
Current time is: {{time.Time}}

Answer to the following questions using JSON syntax, including the data used.
Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
Is it weekend time (weekend/not weekend)?
";

        // This allows to see the prompt before it's sent to OpenAI
        this.WriteLine("--- Rendered Prompt");
        var promptTemplateFactory = new KernelPromptTemplateFactory();
        var promptTemplate = promptTemplateFactory.Create(new PromptTemplateConfig(FunctionDefinition));
        var renderedPrompt = await promptTemplate.RenderAsync(kernel);
        this.WriteLine(renderedPrompt);

        // Run the prompt / prompt function
        var kindOfDay = kernel.CreateFunctionFromPrompt(FunctionDefinition, new OpenAIPromptExecutionSettings() { MaxTokens = 100 });

        // Show the result
        this.WriteLine("--- Prompt Function result");
        var result = await kernel.InvokeAsync(kindOfDay);
        this.WriteLine(result.GetValue<string>());

        /* OUTPUT:

            --- Rendered Prompt

            Today is: Friday, April 28, 2023
            Current time is: 11:04:30 PM

            Answer to the following questions using JSON syntax, including the data used.
            Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
            Is it weekend time (weekend/not weekend)?

            --- Prompt Function result

            {
                "date": "Friday, April 28, 2023",
                "time": "11:04:30 PM",
                "period": "night",
                "weekend": "weekend"
            }
         */
    }

    public Example06_TemplateLanguage(ITestOutputHelper output) : base(output)
    {
    }
}
