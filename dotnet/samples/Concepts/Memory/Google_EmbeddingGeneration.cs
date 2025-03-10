// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using xRetry;

namespace Memory;

// The following example shows how to use Semantic Kernel with Google AI for embedding generation,
// including the ability to specify custom dimensions.
public class Google_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task RunEmbeddingWithDefaultDimensionsAsync()
    {
        Assert.NotNull(TestConfiguration.GoogleAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIEmbeddingGeneration(
                modelId: TestConfiguration.GoogleAI.EmbeddingModelId!,
                apiKey: TestConfiguration.GoogleAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings with the default dimensions for the model
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Length}' dimensions (default) for the provided text");
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task RunEmbeddingWithCustomDimensionsAsync()
    {
        Assert.NotNull(TestConfiguration.GoogleAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        // Specify custom dimensions for the embeddings
        const int CustomDimensions = 512;

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIEmbeddingGeneration(
                modelId: TestConfiguration.GoogleAI.EmbeddingModelId!,
                apiKey: TestConfiguration.GoogleAI.ApiKey,
                dimensions: CustomDimensions);
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings with the specified custom dimensions
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Length}' dimensions (custom: '{CustomDimensions}') for the provided text");

        // Verify that we received embeddings with our requested dimensions
        Assert.Equal(CustomDimensions, embeddings[0].Length);
    }
}
