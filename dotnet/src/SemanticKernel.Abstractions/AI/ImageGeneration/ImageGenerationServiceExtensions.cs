// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.ImageGeneration;

public static class ImageGenerationServiceExtensions
{
    /// <summary>
    /// Adds an image generation service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The IImageGenerationService instance.</param>
    /// <param name="setAsDefault">Optional: set as the default IImageGenerationService</param>
    public static void AddImageGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        IImageGenerationService instance,
        bool setAsDefault = false)
    {
        services.AddSingleton<IImageGenerationService>(serviceId, instance);
    }

    /// <summary>
    /// Adds an image generation service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates IImageGenerationService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default IImageGenerationService</param>
    public static void AddImageGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<IImageGenerationService> factory,
        bool setAsDefault = false)
    {
        services.AddTransient<IImageGenerationService>(serviceId, factory, setAsDefault);

    }

    /// <summary>
    /// Adds an image generation service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates IImageGenerationService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default IImageGenerationService</param>
    public static void AddImageGenerationService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, IImageGenerationService> factory,
        bool setAsDefault = false)
    {
        services.AddTransient<IImageGenerationService>(serviceId, factory, setAsDefault);
    }

    /// <summary>
    /// Get the image generation service matching the given id or the default if an id is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The image generation service id matching the given id or the default.</returns>
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
    /// Remove the image generation service with the given id.
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
    /// Get all registered image generation services.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetImageGenerationServiceIds(this INamedServiceProvider services)
    {
        return services.GetServiceNames<IImageGenerationService>();
    }
}
