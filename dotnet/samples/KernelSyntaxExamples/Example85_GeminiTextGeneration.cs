// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public sealed class Example85_GeminiTextGeneration : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("============= Gemini Text Generation =============");

        await GoogleAIGeminiAsync();
        await VertexAIGeminiAsync();
    }

    private async Task GoogleAIGeminiAsync()
    {
        this.WriteLine("===== Google AI Gemini API =====");

        string geminiApiKey = TestConfiguration.GoogleAI.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null || geminiModelId is null)
        {
            this.WriteLine("Gemini google ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiTextGeneration(
                modelId: geminiModelId,
                apiKey: geminiApiKey)
            .Build();

        await RunSampleAsync(kernel);
    }

    private async Task VertexAIGeminiAsync()
    {
        this.WriteLine("===== Vertex AI Gemini API =====");

        string geminiApiKey = TestConfiguration.VertexAI.BearerKey;
        string geminiModelId = TestConfiguration.VertexAI.Gemini.ModelId;
        string geminiLocation = TestConfiguration.VertexAI.Location;
        string geminiProject = TestConfiguration.VertexAI.ProjectId;

        if (geminiApiKey is null || geminiModelId is null || geminiLocation is null || geminiProject is null)
        {
            this.WriteLine("Gemini vertex ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiTextGeneration(
                modelId: geminiModelId,
                bearerKey: geminiApiKey,
                location: geminiLocation,
                projectId: geminiProject)
            .Build();

        await RunSampleAsync(kernel);
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
                           new KernelArguments(new GeminiPromptExecutionSettings() { MaxTokens = 600 })))
        {
            this.Write(text);
        }

        this.WriteLine("");
    }

    private async Task StreamingTextAsync(Kernel kernel)
    {
        this.WriteLine("======== Streaming Text ========");

        string prompt = @"
Write a short story about a dragon and a knight.
Story should be funny and creative.
Write the story in Spanish.";

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>(prompt,
                           new KernelArguments(new GeminiPromptExecutionSettings() { MaxTokens = 600 })))
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

        string? response = await kernel.InvokePromptAsync<string>("Hi Gemini, what can you do for me?",
            new KernelArguments(new GeminiPromptExecutionSettings() { MaxTokens = 120 }));
        this.WriteLine(response);
    }

    public Example85_GeminiTextGeneration(ITestOutputHelper output) : base(output) { }
}
