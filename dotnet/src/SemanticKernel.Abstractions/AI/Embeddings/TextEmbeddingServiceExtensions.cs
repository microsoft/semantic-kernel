// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
namespace Microsoft.SemanticKernel;

public static class TextEmbeddingServiceExtensions
{
    /// <summary>
    /// Adds an <see cref="AIServiceType"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The <see cref="ITextEmbeddingGenerationService"/> instance.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextEmbeddingGenerationService"/></param>
    public static void AddTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        ITextEmbeddingGenerationService instance,
        bool setAsDefault = false) => services.SetService<ITextEmbeddingGenerationService>(serviceId, instance);

    /// <summary>
    /// Adds a <see cref="ITextEmbeddingGenerationService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextEmbeddingGenerationService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextEmbeddingGenerationService"/></param>
    public static void AddTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<ITextEmbeddingGenerationService> factory,
        bool setAsDefault = false) => services.SetServiceFactory<ITextEmbeddingGenerationService>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Adds a <see cref="ITextEmbeddingGenerationService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextEmbeddingGenerationService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextEmbeddingGenerationService"/></param>
    public static void AddTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, ITextEmbeddingGenerationService> factory,
        bool setAsDefault = false) => services.SetServiceFactory<ITextEmbeddingGenerationService>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Set the default <see cref="ITextEmbeddingGenerationService"/> to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of <see cref="ITextEmbeddingGenerationService"/> to use.</param>
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
    /// Get the <see cref="ITextEmbeddingGenerationService"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The embedding service matching the given id or the default service.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static ITextEmbeddingGenerationService GetTextEmbeddingGenerationServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null) => services.GetNamedServiceOrDefault<ITextEmbeddingGenerationService>(serviceId)
            ?? throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Text embedding service not available");

    /// <summary>
    /// Remove the <see cref="ITextEmbeddingGenerationService"/> with the given <paramref name="serviceId"/>..
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveTextEmbeddingGenerationService(
        this INamedServiceCollection services,
        string serviceId) => services.TryRemove<ITextEmbeddingGenerationService>(serviceId);

    /// <summary>
    /// Remove all <see cref="ITextEmbeddingGenerationService"/> services.
    /// </summary>
    public static void RemoveAllTextEmbeddingGenerationServices(this INamedServiceCollection services)
    {
        services.Clear<ITextEmbeddingGenerationService>();
    }

    /// <summary>
    /// Get all <see cref="ITextEmbeddingGenerationService"/> service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetTextEmbeddingGenerationServiceIds(
        this INamedServiceProvider services) => services.GetServiceNames<ITextEmbeddingGenerationService>();

    /// <summary>
    /// Gets the default <see cref="ITextEmbeddingGenerationService"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="ITextEmbeddingGenerationService"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultTextEmbeddingGenerationServiceId(
        this INamedServiceProvider services) => services.GetDefaultServiceName<ITextEmbeddingGenerationService>();
}
