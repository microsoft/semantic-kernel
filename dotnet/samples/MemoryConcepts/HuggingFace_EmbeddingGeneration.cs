// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using xRetry;

#pragma warning disable format // Format item can be simplified
#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace Memory;

// The following example shows how to use Semantic Kernel with HuggingFace API.
public class HuggingFace_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task RunInferenceApiEmbeddingAsync()
    {
        Console.WriteLine("\n======= Hugging Face Inference API - Embedding Example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceEmbeddingGenerator(
                               model: TestConfiguration.HuggingFace.EmbeddingModelId,
                               apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings for each chunk.
        var embeddings = await embeddingGenerator.GenerateAsync(["John: Hello, how are you?\nRoger: Hey, I'm Roger!"]);

        Console.WriteLine($"Generated {embeddings.Count} embeddings for the provided text");
    }
}
