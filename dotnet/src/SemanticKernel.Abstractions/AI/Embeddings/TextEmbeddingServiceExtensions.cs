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
    /// Adds an <see cref="ITextEmbeddingGeneration"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The <see cref="ITextEmbeddingGeneration"/> instance.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextEmbeddingGeneration"/></param>
    public static void AddTextEmbeddingService(
        this INamedServiceCollection services,
        string serviceId,
        ITextEmbeddingGeneration instance,
        bool setAsDefault = false)
            => services.SetService<ITextEmbeddingGeneration>(serviceId, instance, setAsDefault);

    /// <summary>
    /// Adds a <see cref="ITextEmbeddingGeneration"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextEmbeddingGeneration"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextEmbeddingGeneration"/></param>
    public static void AddTextEmbeddingService(
        this INamedServiceCollection services,
        string serviceId,
        Func<ITextEmbeddingGeneration> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<ITextEmbeddingGeneration>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Adds a <see cref="ITextEmbeddingGeneration"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextEmbeddingGeneration"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextEmbeddingGeneration"/></param>
    public static void AddTextEmbeddingService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, ITextEmbeddingGeneration> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<ITextEmbeddingGeneration>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Set the default <see cref="ITextEmbeddingGeneration"/> to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of <see cref="ITextEmbeddingGeneration"/> to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultTextEmbeddingService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<ITextEmbeddingGeneration>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"A text embedding generation service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the <see cref="ITextEmbeddingGeneration"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The embedding service matching the given id or the default service.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static ITextEmbeddingGeneration GetTextEmbeddingServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null)
            => services.GetNamedServiceOrDefault<ITextEmbeddingGeneration>(serviceId)
                ?? throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Text embedding service not available");

    /// <summary>
    /// Remove the <see cref="ITextEmbeddingGeneration"/> with the given <paramref name="serviceId"/>..
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveTextEmbeddingService(
        this INamedServiceCollection services,
        string serviceId)
            => services.TryRemove<ITextEmbeddingGeneration>(serviceId);

    /// <summary>
    /// Remove all <see cref="ITextEmbeddingGeneration"/> services.
    /// </summary>
    public static void RemoveAllTextEmbeddingServices(this INamedServiceCollection services)
        => services.Clear<ITextEmbeddingGeneration>();

    /// <summary>
    /// Get all <see cref="ITextEmbeddingGeneration"/> service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetTextEmbeddingServiceIds(
        this INamedServiceProvider services)
            => services.GetServiceNames<ITextEmbeddingGeneration>();

    /// <summary>
    /// Gets the default <see cref="ITextEmbeddingGeneration"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="ITextEmbeddingGeneration"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultTextEmbeddingServiceId(
        this INamedServiceProvider services)
            => services.GetDefaultServiceName<ITextEmbeddingGeneration>();

    /// <summary>
    /// Returns true if a <see cref="ITextEmbeddingGeneration"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasTextEmbeddingService(
        this INamedServiceProvider services,
        string? serviceId = null)
            => services.HasServiceName<ITextEmbeddingGeneration>(serviceId);
}
