// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.KernelExtensions;

/// <summary>
/// Kernel extension to configure the semantic memory with custom settings
/// </summary>
public static class MemoryConfiguration
{
    /// <summary>
    /// Set the semantic memory to use the given memory storage. Uses the kernel's default embeddings backend.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="storage">Memory storage</param>
    public static void UseMemory(this IKernel kernel, IMemoryStore<float> storage)
    {
        UseMemory(kernel, kernel.Config.DefaultTextEmbeddingServiceId, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embeddings backend.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingsBackendLabel">Kernel backend label for embedding generation</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The embeddingGenerator object is disposed by the kernel")]
    public static void UseMemory(this IKernel kernel, string? embeddingsBackendLabel, IMemoryStore<float> storage)
    {
        Verify.NotEmpty(embeddingsBackendLabel, "The embedding backend label is empty");

        var embeddingGenerator = kernel.GetService<IEmbeddingGenerator<string, float>>();

        UseMemory(kernel, embeddingGenerator, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embedding generator.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingGenerator">Embedding generator</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "The embeddingGenerator object is disposed by the kernel")]
    public static void UseMemory(this IKernel kernel, IEmbeddingGenerator<string, float> embeddingGenerator, IMemoryStore<float> storage)
    {
        Verify.NotNull(storage, "The storage instance provided is NULL");
        Verify.NotNull(embeddingGenerator, "The embedding generator is NULL");

        kernel.RegisterMemory(new SemanticTextMemory(storage, embeddingGenerator));
    }
}
