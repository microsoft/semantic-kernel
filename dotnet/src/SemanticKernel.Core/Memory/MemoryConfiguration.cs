// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Kernel extension to configure the semantic memory with custom settings
/// </summary>
public static class MemoryConfiguration
{
    /// <summary>
    /// Set the semantic memory to use the given memory storage and embeddings service.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="storage">Memory storage</param>
    /// <param name="embeddingsServiceId">Kernel service id for embedding generation</param>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static void UseMemory(this IKernel kernel, IMemoryStore storage, string? embeddingsServiceId = null)
    {
        var embeddingGenerator = kernel.GetService<ITextEmbeddingGeneration>(embeddingsServiceId);

        UseMemory(kernel, embeddingGenerator, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embedding generator.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingGenerator">Embedding generator</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "The embeddingGenerator object is disposed by the kernel")]
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static void UseMemory(this IKernel kernel, ITextEmbeddingGeneration embeddingGenerator, IMemoryStore storage)
    {
        Verify.NotNull(storage);
        Verify.NotNull(embeddingGenerator);

        kernel.RegisterMemory(new SemanticTextMemory(storage, embeddingGenerator));
    }
}
