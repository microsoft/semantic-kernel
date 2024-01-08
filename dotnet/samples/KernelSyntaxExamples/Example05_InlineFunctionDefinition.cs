// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example05_InlineFunctionDefinition : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this._output.WriteLine("======== Inline Function Definition ========");

        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId is null || openAIApiKey is null)
        {
            this._output.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        /*
         * Example: normally you would place prompt templates in a folder to separate
         *          C# code from natural language code, but you can also define a semantic
         *          function inline if you like.
         */

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        // Function defined using few-shot design pattern
        string promptTemplate = @"
Generate a creative reason or excuse for the given event.
Be creative and be funny. Let your imagination run wild.

Event: I am running late.
Excuse: I was being held ransom by giraffe gangsters.

Event: I haven't been to the gym for a year
Excuse: I've been too busy training my pet dragon.

Event: {{$input}}
";

        var excuseFunction = kernel.CreateFunctionFromPrompt(promptTemplate, new OpenAIPromptExecutionSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        var result = await kernel.InvokeAsync(excuseFunction, new() { ["input"] = "I missed the F1 final race" });
        this._output.WriteLine(result.GetValue<string>());

        result = await kernel.InvokeAsync(excuseFunction, new() { ["input"] = "sorry I forgot your birthday" });
        this._output.WriteLine(result.GetValue<string>());

        var fixedFunction = kernel.CreateFunctionFromPrompt($"Translate this date {DateTimeOffset.Now:f} to French format", new OpenAIPromptExecutionSettings() { MaxTokens = 100 });

        result = await kernel.InvokeAsync(fixedFunction);
        this._output.WriteLine(result.GetValue<string>());
    }

    public Example05_InlineFunctionDefinition(ITestOutputHelper output) : base(output)
    {
    }
}
