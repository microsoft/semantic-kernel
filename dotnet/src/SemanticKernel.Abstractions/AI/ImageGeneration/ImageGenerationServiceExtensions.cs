// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
namespace Microsoft.SemanticKernel;

public static class ImageGenerationServiceExtensions
{
    /// <summary>
    /// Adds an <see cref="IImageGenerationService"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The <see cref="IImageGenerationService"/> instance.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="IImageGenerationService"/></param>
    public static void AddImageGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        IImageGenerationService instance,
        bool setAsDefault = false)
            => services.SetService<IImageGenerationService>(serviceId, instance, setAsDefault);

    /// <summary>
    /// Adds an <see cref="IImageGenerationService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="IImageGenerationService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="IImageGenerationService"/></param>
    public static void AddImageGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<IImageGenerationService> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<IImageGenerationService>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Adds an <see cref="IImageGenerationService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="IImageGenerationService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="IImageGenerationService"/></param>
    public static void AddImageGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, IImageGenerationService> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<IImageGenerationService>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Set the default <see cref="IImageGenerationService"/> service to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of completion service to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultImageGenerationService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<IImageGenerationService>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"Image generation service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the <see cref="IImageGenerationService"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The <see cref="IImageGenerationService"/> id matching the given id or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static IImageGenerationService GetImageGenerationServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null) => services.GetNamedServiceOrDefault<IImageGenerationService>(serviceId)
            ?? throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Image generation service not found");

    /// <summary>
    /// Remove the <see cref="IImageGenerationService"/> with the given <paramref name="serviceId"/>..
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveImageGenerationService(
        this INamedServiceCollection services, string serviceId)
            => services.TryRemove<IImageGenerationService>(serviceId);

    /// <summary>
    /// Remove all image generation services.
    /// </summary>
    public static void RemoveAllImageGenerationServices(
        this INamedServiceCollection services)
            => services.Clear<IImageGenerationService>();

    /// <summary>
    /// Get all registered image generation service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetImageGenerationServiceIds(
        this INamedServiceProvider services)
            => services.GetServiceNames<IImageGenerationService>();

    /// <summary>
    /// Gets the default <see cref="IImageGenerationService"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="IImageGenerationService"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultImageGenerationServiceId(
        this INamedServiceProvider services)
            => services.GetDefaultServiceName<IImageGenerationService>();

    /// <summary>
    /// Returns true if a <see cref="IImageGenerationService"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasImageGenerationService(
        this INamedServiceProvider services,
        string? serviceId = null)
            => services.HasServiceName<IImageGenerationService>(serviceId);
}
