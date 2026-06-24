// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using xRetry;

#pragma warning disable format // Format item can be simplified
#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace Memory;

// The following example shows how to use Semantic Kernel with OpenAI.
public class OpenAI_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task RunEmbeddingAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIEmbeddingGenerator(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId!,
                apiKey: TestConfiguration.OpenAI.ApiKey!);
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings for the specified text.
        var embeddings = await embeddingGenerator.GenerateAsync(["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase."]);

        Console.WriteLine($"Generated {embeddings.Count} embeddings for the provided text");
    }
}
