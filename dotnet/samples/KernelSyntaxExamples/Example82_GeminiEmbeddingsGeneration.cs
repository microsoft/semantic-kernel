#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;

public static class Example82_GeminiEmbeddingsGeneration
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Gemini Chat Completion ========");

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
            Console.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiChatCompletion(
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
            .AddVertexAIGeminiEmbeddingsGeneration(
                modelId: geminiModelId,
                apiKey: geminiApiKey,
                location: geminiLocation,
                projectId: geminiProject)
            .Build();

        await Run(kernel);
    }

    private static async Task Run(Kernel kernel)
    {
        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        ReadOnlyMemory<float> embeddings = await embeddingGenerator.GenerateEmbeddingAsync("Hello world!");
        Console.WriteLine("Embeddings:");
        for (int i = 0; i < embeddings.Span.Length; i++)
        {
            float embedding = embeddings.Span[i];
            Console.WriteLine($"{embedding}");
        }
    }
}
