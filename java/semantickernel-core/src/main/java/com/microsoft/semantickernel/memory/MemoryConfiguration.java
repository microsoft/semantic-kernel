// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;

import java.util.Objects;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/// <summary>
/// Kernel extension to configure the semantic memory with custom settings
/// </summary>
public class MemoryConfiguration {
    /// <summary>
    /// Set the semantic memory to use the given memory storage and embeddings service.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="storage">Memory storage</param>
    /// <param name="embeddingsServiceId">Kernel service id for embedding generation</param>

    /**
     * Set the semantic memory to use the given memory storage and embeddings service.
     *
     * @param kernel {@link Kernel} instance
     * @param storage {@link MemoryStore} instance
     * @param embeddingsServiceId Kernel service id for embedding generation, can be {@code null}
     * @throws NullPointerException if {@code kernel} or {@code storage} is {@code null}
     * @throws com.microsoft.semantickernel.KernelException if there is an error getting the
     *     embedding generation service
     */
    public static void useMemory(
            @Nonnull DefaultKernel kernel,
            @Nonnull MemoryStore storage,
            @Nullable String embeddingsServiceId) {
        Objects.requireNonNull(kernel);
        Objects.requireNonNull(storage);

        @SuppressWarnings("unchecked")
        EmbeddingGeneration<String> embeddingGenerator =
                (EmbeddingGeneration<String>)
                        kernel.getService(embeddingsServiceId, EmbeddingGeneration.class);

        useMemory(kernel, embeddingGenerator, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embedding generator.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingGenerator">Embedding generator</param>
    /// <param name="storage">Memory storage</param>
    /**
     * Set the semantic memory to use the given memory storage and embeddings service.
     *
     * @param kernel {@link Kernel} instance
     * @param embeddingGenerator {@link EmbeddingGeneration} instance
     * @param storage {@link MemoryStore} instance
     * @throws NullPointerException if {@code kernel}, {@code embeddingGenerator}, or {@code
     *     storage} is {@code null}
     */
    public static void useMemory(
            @Nonnull DefaultKernel kernel,
            EmbeddingGeneration<String> embeddingGenerator,
            MemoryStore storage) {
        Objects.requireNonNull(kernel);
        Objects.requireNonNull(embeddingGenerator);
        Objects.requireNonNull(storage);

        kernel.registerMemory(new DefaultSemanticTextMemory(storage, embeddingGenerator));
    }
}
