// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using xRetry;

namespace Memory;

// The following example shows how to use Semantic Kernel with AWS Bedrock API for embedding generation,
// including the ability to specify custom dimensions.
public class AWSBedrock_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This test demonstrates how to use the AWS Bedrock API embedding generation.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task GenerateEmbeddings()
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder()
            .AddBedrockEmbeddingGenerator(modelId: TestConfiguration.Bedrock.EmbeddingModelId! ?? "amazon.titan-embed-text-v1");

        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings with the default dimensions for the model
        var embeddings = await embeddingGenerator.GenerateAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Vector.Length}' dimensions (default for current model) for the provided text");
    }
}
