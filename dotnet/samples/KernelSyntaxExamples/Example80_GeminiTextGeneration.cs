#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

public static class Example80_GeminiTextGeneration
{
    public static async Task RunAsync()
    {
        Console.WriteLine("============= Gemini Text Generation =============");

        await GoogleAIGemini();
        await VertexAIGemini();
    }

    private static async Task GoogleAIGemini()
    {
        Console.WriteLine("===== Google AI Gemini API =====");

        string geminiApiKey = TestConfiguration.GoogleAI.Gemini.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null || geminiModelId is null)
        {
            Console.WriteLine("Gemini google ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiTextGeneration(
                modelId: geminiModelId,
                apiKey: geminiApiKey)
            .Build();

        await Run(kernel);
    }

    private static async Task VertexAIGemini()
    {
        Console.WriteLine("===== Vertex AI Gemini API =====");

        string geminiApiKey = TestConfiguration.VertexAI.Gemini.ApiKey;
        string geminiModelId = TestConfiguration.VertexAI.Gemini.ModelId;
        string geminiLocation = TestConfiguration.VertexAI.Gemini.Location;
        string geminiProject = TestConfiguration.VertexAI.Gemini.ProjectId;

        if (geminiApiKey is null || geminiModelId is null || geminiLocation is null || geminiProject is null)
        {
            Console.WriteLine("Gemini vertex ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiTextGeneration(
                modelId: geminiModelId,
                apiKey: geminiApiKey,
                location: geminiLocation,
                projectId: geminiProject)
            .Build();

        await Run(kernel);
    }

    private static async Task Run(Kernel kernel)
    {
        await SimplePrompt(kernel);
        await FunctionFromPrompt(kernel);
        await StreamingText(kernel);
        await StreamingFunctionFromPrompt(kernel);
    }

    private static async Task StreamingFunctionFromPrompt(Kernel kernel)
    {
        Console.WriteLine("======== Streaming Function From Prompt ========");

        string prompt = "Describe what is GIT and why it is useful. Use simple words. Description should be long.";
        var function = kernel.CreateFunctionFromPrompt(prompt);
        await foreach (string text in kernel.InvokeStreamingAsync<string>(function,
                           new KernelArguments(new GeminiPromptExecutionSettings() { MaxTokens = 600 })))
        {
            Console.Write(text);
        }

        Console.WriteLine("");
    }

    private static async Task StreamingText(Kernel kernel)
    {
        Console.WriteLine("======== Streaming Text ========");

        string prompt = @"
Write a short story about a dragon and a knight.
Story should be funny and creative.
Write the story in Spanish.";

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>(prompt,
                           new KernelArguments(new GeminiPromptExecutionSettings() { MaxTokens = 600 })))
        {
            Console.Write(text);
        }

        Console.WriteLine("");
    }

    private static async Task FunctionFromPrompt(Kernel kernel)
    {
        Console.WriteLine("======== Function From Prompt ========");

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
        Console.WriteLine(response);
    }

    private static async Task SimplePrompt(Kernel kernel)
    {
        Console.WriteLine("======== Simple Prompt ========");

        string? response = await kernel.InvokePromptAsync<string>("Hi Gemini, what can you do for me?",
            new KernelArguments(new GeminiPromptExecutionSettings() { MaxTokens = 120 }));
        Console.WriteLine(response);
    }
}
