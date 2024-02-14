// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Xunit;
using Xunit.Abstractions;

public class Example80_OllamaTextGeneration : BaseTest
{
    [Fact]
    public Task RunAsync()
    {
        this.WriteLine("============= Ollama Text Generation =============");

        string modelId = TestConfiguration.Ollama.ModelId;
        Uri? baseUri = TestConfiguration.Ollama.BaseUri;

        if (modelId is null || baseUri is null)
        {
            this.WriteLine("Ollama configuration not found. Skipping example.");
            return Task.CompletedTask;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextGeneration(
                modelId: modelId,
                baseUri: baseUri)
            .Build();

        return RunSampleAsync(kernel);
    }
    private async Task RunSampleAsync(Kernel kernel)
    {
        await SimplePromptAsync(kernel);
        await FunctionFromPromptAsync(kernel);
        await StreamingTextAsync(kernel);
        await StreamingFunctionFromPromptAsync(kernel);
    }

    private async Task StreamingFunctionFromPromptAsync(Kernel kernel)
    {
        this.WriteLine("======== Streaming Function From Prompt ========");

        string prompt = "Describe what is GIT and why it is useful. Use simple words. Description should be long.";
        var function = kernel.CreateFunctionFromPrompt(prompt);
        await foreach (string text in kernel.InvokeStreamingAsync<string>(function,
                           new KernelArguments(new OllamaPromptExecutionSettings() { MaxTokens = 600 })))
        {
            this.Write(text);
        }

        this.WriteLine();
    }

    private async Task StreamingTextAsync(Kernel kernel)
    {
        this.WriteLine("======== Streaming Text ========");

        string prompt = @"
Write a short story about a dragon and a knight.
Story should be funny and creative.
Write the story in Spanish.";

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>(prompt,
                           new KernelArguments(new OllamaPromptExecutionSettings() { MaxTokens = 600 })))
        {
            this.Write(text);
        }

        this.WriteLine("");
    }

    private async Task FunctionFromPromptAsync(Kernel kernel)
    {
        this.WriteLine("======== Function From Prompt ========");

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

        var function = kernel.CreateFunctionFromPrompt(promptTemplate);
        string? response = await kernel.InvokeAsync<string>(function,
            new KernelArguments() { ["Input"] = "sorry I forgot your birthday" });
        this.WriteLine(response);
    }

    private async Task SimplePromptAsync(Kernel kernel)
    {
        this.WriteLine("======== Simple Prompt ========");

        string? response = await kernel.InvokePromptAsync<string>("Hi Ollama, what can you do for me?",
            new KernelArguments(new OllamaPromptExecutionSettings() { MaxTokens = 120 }));
        this.WriteLine(response);
    }

    public Example80_OllamaTextGeneration(ITestOutputHelper output) : base(output)
    {
    }
}
