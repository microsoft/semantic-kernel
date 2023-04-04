// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel;

/// <summary>
/// Kernel extension to configure the semantic memory with custom settings
/// </summary>
public static class MemoryConfiguration
{
    /// <summary>
    /// Set the semantic memory to use the given memory storage. Uses the kernel's default embeddings service.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="storage">Memory storage</param>
    public static void UseMemory(this IKernel kernel, IMemoryStore storage)
    {
        UseMemory(kernel, kernel.Config.DefaultTextEmbeddingGenerationServiceId, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embeddings service.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingsServiceId">Kernel service id for embedding generation</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The embeddingGenerator object is disposed by the kernel")]
    public static void UseMemory(this IKernel kernel, string? embeddingsServiceId, IMemoryStore storage)
    {
        Verify.NotEmpty(embeddingsServiceId, "The embedding service id is empty");

        var embeddingGenerator = kernel.GetService<IEmbeddingGeneration<string, float>>();

        UseMemory(kernel, embeddingGenerator, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embedding generator.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingGenerator">Embedding generator</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "The embeddingGenerator object is disposed by the kernel")]
    public static void UseMemory(this IKernel kernel, IEmbeddingGeneration<string, float> embeddingGenerator, IMemoryStore storage)
    {
        Verify.NotNull(storage, "The storage instance provided is NULL");
        Verify.NotNull(embeddingGenerator, "The embedding generator is NULL");

        kernel.RegisterMemory(new SemanticTextMemory(storage, embeddingGenerator));
    }
}
