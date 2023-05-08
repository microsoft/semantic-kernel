// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
namespace Microsoft.SemanticKernel;

public static class TextEmbeddingServiceExtensions
{
    /// <summary>
    /// Get the <see cref="ITextEmbeddingGeneration"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The embedding service matching the given id or the default service.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static ITextEmbeddingGeneration GetTextEmbeddingServiceOrDefault(
        this IAIServiceProvider services,
        string? serviceId = null)
            => services.GetNamedServiceOrDefault<ITextEmbeddingGeneration>(serviceId)
                ?? throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Text embedding service not available");

    /// <summary>
    /// Returns true if a <see cref="ITextEmbeddingGeneration"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasTextEmbeddingService(
        this IAIServiceProvider services,
        string? serviceId = null)
            => services.TryGetService<ITextEmbeddingGeneration>(serviceId, out _);
}
