// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using xRetry;

namespace Memory;

// The following example shows how to use Semantic Kernel with Google.GenAI and Microsoft.Extensions.AI for embedding generation,
// including the ability to specify custom dimensions.
public class Google_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This test demonstrates how to use the Google Vertex AI embedding generator with default dimensions.
    /// </summary>
    [RetryFact]
    public async Task GenerateEmbeddingWithDefaultDimensionsUsingVertexAI()
    {
        Assert.NotNull(TestConfiguration.VertexAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);

        // The Google SDK discovers application default credentials and refreshes tokens automatically.
        using var googleClient = new Google.GenAI.Client(
            vertexAI: true,
            project: TestConfiguration.VertexAI.ProjectId,
            location: TestConfiguration.VertexAI.Location);
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddEmbeddingGenerator(googleClient.AsIEmbeddingGenerator(TestConfiguration.VertexAI.EmbeddingModelId!));
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings with the default dimensions for the model
        var embeddings = await embeddingGenerator.GenerateAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Vector.Length}' dimensions (default) for the provided text");
    }

    [RetryFact]
    public async Task GenerateEmbeddingWithDefaultDimensionsUsingGoogleAI()
    {
        Assert.NotNull(TestConfiguration.GoogleAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddEmbeddingGenerator(googleClient.AsIEmbeddingGenerator(TestConfiguration.GoogleAI.EmbeddingModelId!));
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings with the default dimensions for the model
        var embeddings = await embeddingGenerator.GenerateAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Vector.Length}' dimensions (default) for the provided text");
    }

    [RetryFact]
    public async Task GenerateEmbeddingWithCustomDimensionsUsingGoogleAI()
    {
        Assert.NotNull(TestConfiguration.GoogleAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        // Specify custom dimensions for the embeddings
        const int CustomDimensions = 512;

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddEmbeddingGenerator(
            googleClient.AsIEmbeddingGenerator(TestConfiguration.GoogleAI.EmbeddingModelId!, defaultModelDimensions: CustomDimensions));
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings with the specified custom dimensions
        var embeddings = await embeddingGenerator.GenerateAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Vector.Length}' dimensions (custom: '{CustomDimensions}') for the provided text");

        // Verify that we received embeddings with our requested dimensions
        Assert.Equal(CustomDimensions, embeddings[0].Vector.Length);
    }
}
