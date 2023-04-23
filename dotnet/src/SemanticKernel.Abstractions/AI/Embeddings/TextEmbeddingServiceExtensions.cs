// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.Embeddings;

public static class TextEmbeddingServiceExtensions
{
    /// <summary>
    /// Adds an text embedding generation service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The ITextEmbeddingGenerationService instance.</param>
    /// <param name="setAsDefault">Optional: set as the default ITextEmbeddingGenerationService</param>
    public static void AddTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        ITextEmbeddingGenerationService instance,
        bool setAsDefault = false)
    {
        services.AddSingleton<ITextEmbeddingGenerationService>(serviceId, instance);
    }

    /// <summary>
    /// Adds an text embedding generation service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates ITextEmbeddingGenerationService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default ITextEmbeddingGenerationService</param>
    public static void AddTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<ITextEmbeddingGenerationService> factory,
        bool setAsDefault = false)
    {
        services.AddTransient<ITextEmbeddingGenerationService>(serviceId, factory, setAsDefault);

    }

    /// <summary>
    /// Adds an text embedding generation service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates ITextEmbeddingGenerationService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default ITextEmbeddingGenerationService</param>
    public static void AddTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, ITextEmbeddingGenerationService> factory,
        bool setAsDefault = false)
    {
        services.AddTransient<ITextEmbeddingGenerationService>(serviceId, factory, setAsDefault);
    }

    /// <summary>
    /// Set the default embedding service to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of text embedding service to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<ITextEmbeddingGenerationService>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"A text embedding generation service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the text embedding service matching the given id or the default if an id is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The embedding service matching the given id or the default service.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static ITextEmbeddingGenerationService GetTextEmbeddingGenerationServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null)
    {
        return services.GetNamedServiceOrDefault<ITextEmbeddingGenerationService>(serviceId)
            ?? throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "Text embedding service not available");
    }

    /// <summary>
    /// Remove the image generation service with the given id.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveTextEmbeddingGenerationService(this INamedServiceCollection services, string serviceId)
    {
        return services.TryRemove<ITextEmbeddingGenerationService>(serviceId);
    }

    /// <summary>
    /// Remove all text embedding generation services.
    /// </summary>
    public static void RemoveAllTextEmbeddingGenerationServices(this INamedServiceCollection services)
    {
        services.Clear<ITextEmbeddingGenerationService>();
    }

    /// <summary>
    /// Get all text embedding generation services.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetTextEmbeddingServiceIds(this INamedServiceProvider services)
    {
        return services.GetServiceNames<ITextEmbeddingGenerationService>();
    }
}
