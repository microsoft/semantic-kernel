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

        string geminiApiKey = TestConfiguration.Gemini.ApiKey;
        string geminiEmbeddingModelId = TestConfiguration.Gemini.EmbeddingModelId;

        if (geminiApiKey is null || geminiEmbeddingModelId is null)
        {
            Console.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIGeminiEmbeddingsGeneration(
                modelId: geminiEmbeddingModelId,
                apiKey: geminiApiKey)
            .Build();

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
