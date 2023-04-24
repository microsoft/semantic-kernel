// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.ImageGeneration;

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
    {
        services.SetSingleton<IImageGenerationService>(serviceId, instance);
    }

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
    {
        services.SetTransient<IImageGenerationService>(serviceId, factory, setAsDefault);

    }

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
    {
        services.SetTransient<IImageGenerationService>(serviceId, factory, setAsDefault);
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
        string? serviceId = null)
    {
        return services.GetNamedServiceOrDefault<IImageGenerationService>(serviceId)
            ?? throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "Image generation service not found");
    }

    /// <summary>
    /// Remove the <see cref="IImageGenerationService"/> with the given <paramref name="serviceId"/>..
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveImageGenerationService(this INamedServiceCollection services, string serviceId)
    {
        return services.TryRemove<IImageGenerationService>(serviceId);
    }

    /// <summary>
    /// Remove all image generation services.
    /// </summary>
    public static void RemoveAllImageGenerationServices(this INamedServiceCollection services)
    {
        services.Clear<IImageGenerationService>();
    }

    /// <summary>
    /// Get all registered image generation service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetImageGenerationServiceIds(this INamedServiceProvider services)
    {
        return services.GetServiceNames<IImageGenerationService>();
    }

    /// <summary>
    /// Gets the default <see cref="IImageGenerationService"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="IImageGenerationService"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultImageGenerationServiceId(this INamedServiceProvider services)
    {
        return services.GetDefaultServiceName<IImageGenerationService>();
    }
}
