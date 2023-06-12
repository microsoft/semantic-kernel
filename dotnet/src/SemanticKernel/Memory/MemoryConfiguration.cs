// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
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
    public static void UseMemory(this IKernel kernel, ITextEmbeddingGeneration embeddingGenerator, IMemoryStore storage)
    {
        Verify.NotNull(storage);
        Verify.NotNull(embeddingGenerator);

        var memory = CreateSemanticTextMemory(storage, embeddingGenerator);

        kernel.RegisterMemory(memory);
    }

    /// <summary>
    /// Create <see cref="SemanticTextMemory"/> or <see cref="SemanticTextMemory{TFilter}"/> based on <paramref name="memoryStore"/>.
    /// </summary>
    /// <param name="memoryStore">Memory storage</param>
    /// <param name="embeddingGenerator">Embedding generator</param>
    /// <returns></returns>
    private static ISemanticTextMemory CreateSemanticTextMemory(IMemoryStore memoryStore, ITextEmbeddingGeneration embeddingGenerator)
    {
        var memoryStoreType = memoryStore.GetType();
        var filterableMemoryStoreInterfaceType = memoryStoreType
            .GetInterfaces()
            .SingleOrDefault(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IMemoryStore<>));

        if (filterableMemoryStoreInterfaceType != null)
        {
            var filterType = filterableMemoryStoreInterfaceType
                .GetGenericArguments()
                .Single();

            var textEmbeddingGenerationType = typeof(ITextEmbeddingGeneration);
            var filterableSemanticTextMemoryType = typeof(SemanticTextMemory<>).MakeGenericType(filterType);
            var constructor = filterableSemanticTextMemoryType.GetConstructor(new[] { memoryStoreType, textEmbeddingGenerationType });
            if (constructor == null)
            {
                throw new System.InvalidOperationException(
                    $"No {filterableSemanticTextMemoryType.FullName} constructor with parameter types: {memoryStoreType.FullName}, {textEmbeddingGenerationType.FullName} found.");
            }

            return (ISemanticTextMemory)constructor.Invoke(new object[] { memoryStore, embeddingGenerator });
        }

        return new SemanticTextMemory(memoryStore, embeddingGenerator);
    }
}
