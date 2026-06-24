// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Memory;

// The following example shows how to use Semantic Kernel with Onnx GenAI API.
public class Onnx_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Example using the service directly to get embeddings
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>EmbeddingModelPath:</term>
    /// <description>D:\huggingface\bge-micro-v2\onnx\model.onnx</description>
    /// </item>
    /// <item>
    /// <term>EmbeddingVocabPath:</term>
    /// <description>D:\huggingface\bge-micro-v2\vocab.txt</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task RunEmbeddingAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.EmbeddingModelPath); // dotnet user-secrets set "Onnx:EmbeddingModelPath" "<model-file-path>"
        Assert.NotNull(TestConfiguration.Onnx.EmbeddingVocabPath); // dotnet user-secrets set "Onnx:EmbeddingVocabPath" "<vocab-file-path>"

        Console.WriteLine("\n======= Onnx - Embedding Example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddBertOnnxEmbeddingGenerator(TestConfiguration.Onnx.EmbeddingModelPath, TestConfiguration.Onnx.EmbeddingVocabPath)
            .Build();

        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings for each chunk.
        var embeddings = await embeddingGenerator.GenerateAsync(["John: Hello, how are you?\nRoger: Hey, I'm Roger!"]);

        Console.WriteLine($"Generated {embeddings.Count} embeddings for the provided text");
    }

    /// <summary>
    /// Example using the service collection directly to get embeddings
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>EmbeddingModelPath:</term>
    /// <description>D:\huggingface\bge-micro-v2\onnx\model.onnx</description>
    /// </item>
    /// <item>
    /// <term>EmbeddingVocabPath:</term>
    /// <description>D:\huggingface\bge-micro-v2\vocab.txt</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task RunServiceCollectionEmbeddingAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.EmbeddingModelPath); // dotnet user-secrets set "Onnx:EmbeddingModelPath" "<model-file-path>"
        Assert.NotNull(TestConfiguration.Onnx.EmbeddingVocabPath); // dotnet user-secrets set "Onnx:EmbeddingVocabPath" "<vocab-file-path>"

        Console.WriteLine("\n======= Onnx - Embedding Example ========\n");

        var services = new ServiceCollection()
            .AddBertOnnxEmbeddingGenerator(TestConfiguration.Onnx.EmbeddingModelPath, TestConfiguration.Onnx.EmbeddingVocabPath);
        var provider = services.BuildServiceProvider();
        var embeddingGenerator = provider.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Generate embeddings for each chunk.
        var embeddings = await embeddingGenerator.GenerateAsync(["John: Hello, how are you?\nRoger: Hey, I'm Roger!"]);

        Console.WriteLine($"Generated {embeddings.Count} embeddings for the provided text");
    }
}
