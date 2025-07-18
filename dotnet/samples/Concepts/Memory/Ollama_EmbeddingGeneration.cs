// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using xRetry;

namespace Memory;

// The following example shows how to use Semantic Kernel with Ollama API.
public class Ollama_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task RunEmbeddingAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.EmbeddingModelId);

        Console.WriteLine("\n======= Ollama - Embedding Example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaEmbeddingGenerator(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: TestConfiguration.Ollama.EmbeddingModelId)
            .Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings for each chunk.
        var embeddings = await embeddingGenerator.GenerateAsync(["John: Hello, how are you?\nRoger: Hey, I'm Roger!"]);

        Console.WriteLine($"Generated {embeddings.Count} embeddings for the provided text");
    }
}
