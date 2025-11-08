// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.VoyageAI;

namespace Reranking;

/// <summary>
/// Example demonstrating VoyageAI reranking with Semantic Kernel.
/// </summary>
public class VoyageAI_Reranking(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RerankDocumentsAsync()
    {
        // Get API key from environment
        var apiKey = Environment.GetEnvironmentVariable("VOYAGE_AI_API_KEY")
            ?? throw new InvalidOperationException("Please set the VOYAGE_AI_API_KEY environment variable");

        // Create reranking service
        var rerankingService = new VoyageAITextRerankingService(
            modelId: "rerank-2.5",
            apiKey: apiKey
        );

        // Define query and documents
        var query = "What are the key features of Semantic Kernel?";

        var documents = new List<string>
        {
            "Semantic Kernel is an open-source SDK that lets you easily build agents that can call your existing code.",
            "The capital of France is Paris, a beautiful city known for its art and culture.",
            "Python is a high-level, interpreted programming language with dynamic typing.",
            "Semantic Kernel provides enterprise-ready AI orchestration with model flexibility and plugin ecosystem.",
            "Machine learning models require large amounts of data for training."
        };

        Console.WriteLine($"Query: {query}\n");
        Console.WriteLine("Documents to rerank:");
        for (int i = 0; i < documents.Count; i++)
        {
            Console.WriteLine($"{i + 1}. {documents[i]}");
        }

        // Rerank documents
        var results = await rerankingService.RerankAsync(query, documents);

        Console.WriteLine("\nReranked results (sorted by relevance):");
        for (int i = 0; i < results.Count; i++)
        {
            var result = results[i];
            Console.WriteLine($"\n{i + 1}. Score: {result.RelevanceScore:F4}");
            Console.WriteLine($"   Original Index: {result.Index}");
            Console.WriteLine($"   Text: {result.Text}");
        }
    }
}
