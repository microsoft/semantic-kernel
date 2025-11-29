// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.VoyageAI;

namespace Embeddings;

/// <summary>
/// Example demonstrating VoyageAI text embeddings with Semantic Kernel.
/// </summary>
public class VoyageAI_TextEmbedding(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GenerateTextEmbeddingsAsync()
    {
        // Get API key from environment
        var apiKey = Environment.GetEnvironmentVariable("VOYAGE_AI_API_KEY")
            ?? throw new InvalidOperationException("Please set the VOYAGE_AI_API_KEY environment variable");

        // Create embedding service
        var embeddingService = new VoyageAITextEmbeddingGenerationService(
            modelId: "voyage-3-large",
            apiKey: apiKey
        );

        // Generate embeddings
        var texts = new List<string>
        {
            "Semantic Kernel is an SDK for integrating AI models",
            "VoyageAI provides high-quality embeddings",
            "C# is a modern, object-oriented programming language"
        };

        Console.WriteLine("Generating embeddings for:");
        for (int i = 0; i < texts.Count; i++)
        {
            Console.WriteLine($"{i + 1}. {texts[i]}");
        }

        var embeddings = await embeddingService.GenerateEmbeddingsAsync(texts);

        Console.WriteLine($"\nGenerated {embeddings.Count} embeddings");
        Console.WriteLine($"Embedding dimension: {embeddings[0].Length}");
        Console.WriteLine($"First embedding (first 5 values): [{string.Join(", ", embeddings[0].Span[..5].ToArray())}]");
    }
}
